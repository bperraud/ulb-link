from celery import shared_task
from link.models import User
from django.utils.html import strip_tags
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from link.context_processors import get_host
from django.db.models import Prefetch
from link.models import Link, NextcloudShareBatchJob

from xml.etree import ElementTree as ET
from urllib.parse import unquote

from mycloud.utils import (
    get_or_create_share_in_nextcloud,
    mycloud_api,
    update_shares_object,
)
from permalink.utils import *
from types import SimpleNamespace

import logging

logger = logging.getLogger(__name__)


@shared_task
def validate_all_links():
    users = User.objects.exclude(unsubscribe_from_email=True).prefetch_related(
        Prefetch("link", queryset=Link.objects.filter(share__isnull=True))
    )
    for user in users:
        invalid_links = []
        for link in user.link.all():
            if not link.is_valid:
                link.is_target_url_reachable()
                invalid_links.append(link)
            link.is_target_url_reachable()  # do not append before the test so it needs two consecutive days to send email
        if invalid_links:
            send_invalid_link_mail(user, invalid_links)


def send_invalid_link_mail(user: User, invalid_links):
    context = {
        "invalid_links": invalid_links,
        "site_domain": get_host(),
        "user": user,
        "token": str(user.id) + "." + sign(str(user.id)),
    }
    html_content = render_to_string("email/invalid_links.html", context)

    send_email(
        "Liens invalides détectés dans Permalink",
        html_content,
        [user.email],
    )


def send_deletion_warning_mail(deleted_link):
    context = {
        "deleted_link": deleted_link,
        "site_domain": get_host(),
        "user": deleted_link.user,
        "token": str(deleted_link.user.id) + "." + sign(str(deleted_link.user.id)),
    }
    html_content = render_to_string("email/warning_deletion.html", context)

    send_email(
        "Suppression automatique d’un permalien",
        html_content,
        [deleted_link.user.email],
    )


def send_email(subject, html_content, recipient_list: list):
    if settings.DEBUG:
        recipient_list = settings.ADMINS

    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=None,
        to=recipient_list,
    )

    email.attach_alternative(html_content, "text/html")
    email.send()


def parse_xml(content, job, requested_folder):
    root = ET.fromstring(content)
    ns = {"d": "DAV:"}
    base = f"/remote.php/dav/files/{job.user.username}"

    for response in root.findall("d:response", ns):
        href = response.findtext("d:href", namespaces=ns)
        if not href:
            continue
        path = unquote(href)[len(base) :].rstrip("/")
        # Skip the folder we requested
        if path == requested_folder.rstrip("/"):
            continue
        is_folder = (
            response.find(
                "d:propstat/d:prop/d:resourcetype/d:collection",
                ns,
            )
            is not None
        )

        if is_folder:
            job.directories_to_scan.append(path)
        else:
            job.file_paths.append(path)
            job.initial_file_count += 1

    return job


# each 10 minutes : creates max 100 shares (per user)
@shared_task
def process_bulk_share_creation():
    jobs = NextcloudShareBatchJob.objects.all()

    for job in jobs:
        folders = job.directories_to_scan.copy()
        job.directories_to_scan = []
        request = SimpleNamespace(user=job.user)
        for folder in folders:
            xml_content = mycloud_api.get_directory_files(request, folder)
            parse_xml(xml_content, job, folder)
        job.save()

    for job in jobs:
        paths_to_process = job.file_paths[:100]
        remaining = job.file_paths[100:]
        request = SimpleNamespace(user=job.user)

        for file in paths_to_process:
            try:
                share = get_or_create_share_in_nextcloud(request, file)
                Link.objects.get_or_create(
                    user=job.user,
                    share=share,
                )
            except Exception:
                logger.exception("Error while creating permalink")
                remaining.append(file)  # retry later

        if remaining:
            job.file_paths = remaining
            job.save(update_fields=["file_paths"])
        else:
            job.delete()


@shared_task
def sync_user_shares(user_id: str):
    try:
        user = User.objects.get(id=user_id)
        request = SimpleNamespace(user=user)
        response = mycloud_api.get_shares(request)
        update_shares_object(response.json())
    except Exception:
        logger.exception("Error sync user shares")
