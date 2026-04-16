from celery import shared_task
from link.models import Link, User
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from django.shortcuts import render
from link.context_processors import get_host

from django.core import mail


@shared_task
def validate_all_links(name="test"):
    for user in User.objects.all():
        invalid_links = []
        for link in Link.objects.filter(user=user):
            if not link.self_test():
                invalid_links.append(link)


def test_mail(request):
    return render(
        request,
        "email/mail.html",
        {"invalid_links": Link.objects.all(), "site_domain": get_host()},
    )


def send_test_mail():

    html_content = render_to_string("email/mail.html")
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject="Nouvelle activité",
        body=text_content,
        from_email=None,
        to=["benjamin.perraudin@ulb.be"],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()


def send_email():

    subject = "Subject"
    html_message = render_to_string("email/mail.html", {"context": "values"})
    plain_message = strip_tags(html_message)

    mail.send_mail(
        subject,
        plain_message,
        None,
        ["benjamin.perraudin@ulb.be"],
        html_message=html_message,
    )
