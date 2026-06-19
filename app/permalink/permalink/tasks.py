from celery import shared_task
from link.models import User
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from link.context_processors import get_host
from django.db.models import Prefetch
from link.models import Link, NextcloudShareBatchJob

from link.views.nextcloud_utils import get_or_create_share_in_nextcloud
from permalink.utils import *
from types import SimpleNamespace
from link.views.nextcloud_utils import update_shares_object

from link.views.nextcloud_utils import (
    mycloud_api,
)


@shared_task
def validate_all_links():
    users = User.objects.exclude(unsubscribe_from_email=True).prefetch_related(
        Prefetch("link", queryset=Link.objects.filter(share__isnull=True))
    )
    for user in users:
        invalid_links = []
        for link in user.link.all():
            link.save()
            if not link.is_valid:
                invalid_links.append(link)
        if invalid_links:
            send_invalid_link_mail(user, invalid_links)


def send_invalid_link_mail(user: User, invalid_links):
    context = {
        "invalid_links": invalid_links,
        "site_domain": get_host(),
        "user": user,
        "token": str(user.id) + "." + sign(str(user.id)),
    }
    html_content = render_to_string("email/mail.html", context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject="Liens invalides détectés dans Permalink",
        body=text_content,
        from_email=None,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()


# each 10 minutes : creates max 100 shares (per user)
@shared_task
def process_bulk_share_creation():
    jobs = NextcloudShareBatchJob.objects.all()

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
            except Exception as e:
                print("Error while creating permalink : " + str(e))
                remaining.append(file)  # retry later

        if remaining:
            job.file_paths = remaining
            job.save(update_fields=["file_paths"])
        else:
            job.delete()


# @shared_task
# def sync_user_shares(response):
#     try:
#         update_shares_object(response)
#     except:
#         print("Error sync user shares")


@shared_task
def sync_user_shares(user: User):
    try:
        request = SimpleNamespace(user=user)
        response = mycloud_api.get_shares(request)
        update_shares_object(response)
    except:
        print("Error sync user shares")
