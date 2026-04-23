from celery import shared_task
from link.models import Link, User
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.shortcuts import render
from link.context_processors import get_host
from link.auth import get_valid_access_token
from django.conf import settings


class NextcloudError(Exception):
    pass


class NotAuthenticated(Exception):
    pass


@shared_task
def validate_all_links():
    users = User.objects.prefetch_related("link")
    for user in users:
        invalid_links = []
        for link in user.link.all():
            link.save()
            if not link.is_valid:
                invalid_links.append(link)
        context = {"invalid_links": invalid_links, "site_domain": get_host()}
        if invalid_links:
            send_test_mail(user, context)


import requests
from xml.etree import ElementTree as ET
from urllib.parse import unquote


def webdav_to_jstree(xml, username):
    ns = {"d": "DAV:"}
    root = ET.fromstring(xml)

    base = f"/remote.php/dav/files/{username}/"

    nodes = []

    for resp in root.findall("d:response", ns):
        href_el = resp.find("d:href", ns)
        if href_el is None:
            continue

        href = href_el.text

        # Extract relative path
        if not href.startswith(base):
            continue

        rel_path = href[len(base) :]  # remove prefix
        rel_path = unquote(rel_path).rstrip("/")

        # Root folder
        if rel_path == "":
            path = "/"
            name = username
            parent = "#"
        else:
            path = "/" + rel_path
            name = rel_path.split("/")[-1]

            # Compute parent correctly
            parent_path = "/" + rel_path.rsplit("/", 1)[0] if "/" in rel_path else "/"
            parent = parent_path

        nodes.append({"id": path, "parent": parent, "text": name})

    return {"data": nodes}


def get_nextcloud_files(request):
    access_token = get_valid_access_token(request)
    if not access_token:
        raise NotAuthenticated()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Depth": "1",
        "Content-Type": "application/xml",
    }

    xml_body = """<?xml version="1.0"?>
    <d:propfind xmlns:d="DAV:">
      <d:prop>
        <d:getlastmodified/>
        <d:getcontentlength/>
        <d:resourcetype/>
      </d:prop>
    </d:propfind>
    """
    try:
        response = requests.request(
            headers=headers,
            method="PROPFIND",
            url=f"{settings.NEXTCLOUD_URL}/remote.php/dav/files/{request.user.username}",
            data=xml_body,
        )
    except:
        raise NextcloudError("Error reaching Nextcloud Api")
    if response.status_code > 300:
        raise NextcloudError("Error reaching Nextcloud Api")

    print(response.content)
    return response.content


def test_profind(request):
    response = get_nextcloud_files(request)
    tree_data = webdav_to_jstree(response, request.user.username)

    return render(request, "jstree.html", tree_data)


def send_test_mail(user: User, context: dict):
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
