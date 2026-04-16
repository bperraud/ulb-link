from celery import shared_task
from link.models import Link, User
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from django.shortcuts import render
from link.context_processors import get_host

from django.core import mail

from django_celery_beat.models import (
    PeriodicTask,
    CrontabSchedule,
)
from permalink.settings import TIME_ZONE

# crontab, _ = CrontabSchedule.objects.get_or_create(
#     minute="30",
#     hour="8",
#     day_of_week="*",
#     day_of_month="*",
#     month_of_year="*",
#     timezone=TIME_ZONE,
# )

# PeriodicTask.objects.get_or_create(
#     crontab=crontab,
#     name="Validate URLs",
#     task="permalink.tasks.validate_all_links",
# )


@shared_task
def validate_all_links(name="test"):
    for user in User.objects.all():
        invalid_links = []
        for link in Link.objects.filter(user=user):
            if not link.self_test():
                invalid_links.append(link)


@shared_task
def fast_validate_all_links(name="fasttest"):
    users = User.objects.prefetch_related("link_set")
    for user in users:
        invalid_links = []
        for link in user.link_set.all():
            if not link.self_test():
                invalid_links.append(link)


def test_mail(request):
    return render(
        request,
        "email/mail.html",
        {"invalid_links": Link.objects.all(), "site_domain": get_host()},
    )


def send_test_mail(user: User, context: dict):

    html_content = render_to_string("email/mail.html")
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject="Nouvelle activité",
        body=text_content,
        from_email=None,
        to=[user.email],
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
