from celery import shared_task
from link.models import Link


@shared_task
def validate_url(name="test"):
    for link in Link.objects.all():
        if not link.self_test():
            print("this link doesnt work")
