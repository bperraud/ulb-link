from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from permalink.settings import TIME_ZONE


class Command(BaseCommand):
    help = "Create or update periodic tasks"

    def handle(self, *args, **options):

        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute="30",
            hour="8",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
            timezone=TIME_ZONE,
        )

        PeriodicTask.objects.get_or_create(
            crontab=crontab,
            name="Validate URLs",
            task="permalink.tasks.validate_all_links",
        )

        self.stdout.write(self.style.SUCCESS("Periodic task ensured"))
