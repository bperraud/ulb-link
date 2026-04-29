from celery import shared_task
from link.models import User
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.shortcuts import render
from link.context_processors import get_host
from django.db.models import Prefetch
from link.models import Link


@shared_task
def validate_all_links():
    users = User.objects.prefetch_related(
        Prefetch("link", queryset=Link.objects.filter(share__isnull=True))
    )
    for user in users:
        invalid_links = []
        for link in user.link.all():
            link.save()
            if not link.is_valid:
                invalid_links.append(link)
        context = {"invalid_links": invalid_links, "site_domain": get_host()}
        if invalid_links:
            send_invalid_link_mail(user, context)


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
