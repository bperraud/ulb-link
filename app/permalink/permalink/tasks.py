from celery import shared_task
from link.models import User
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.shortcuts import render
from link.context_processors import get_host
from link.utils import webdav_to_jstree

from link.views.nextcloud_views import get_nextcloud_files, create_share_in_nextcloud


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
            send_invalid_link_mail(user, context)


def test_profind(request):
    response = get_nextcloud_files(request)
    tree_data = webdav_to_jstree(response, request.user)

    create_share_in_nextcloud(request, "/Assistant/2026-02-20_08.52.46 recording.wav")

    return render(request, "jstree.html", tree_data)


def send_invalid_link_mail(user: User, context: dict):
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
