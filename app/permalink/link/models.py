from django.db import models

# from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
import string, random

from link.context_processors import get_host
from django.db.models.signals import post_delete
from django.dispatch import receiver

from django.contrib.auth.models import AbstractUser
from django.conf import settings
import requests


class User(AbstractUser):
    is_nextcloud_user = models.BooleanField(default=False)


class Share(models.Model):
    uid = models.IntegerField(primary_key=True)
    target_url = models.URLField(verbose_name="Target URL")
    path = models.CharField()
    expiration = models.DateTimeField(null=True)


class Link(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="link"
    )

    share = models.ForeignKey(
        Share,
        on_delete=models.SET_NULL,
        related_name="share",
        null=True,
        blank=True,
        help_text="Reference to a Share object, if applicable.",
    )

    direct_target_url = models.URLField(
        null=True,
        blank=True,
        verbose_name="Direct Target URL",
        help_text="Used if no Share is associated.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    token = models.CharField(
        validators=[MinLengthValidator(8)],
        max_length=20,
        verbose_name="Token",
        unique=True,
        null=False,
    )

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self._generate_unique_token()
        super().save(*args, **kwargs)

    def _generate_unique_token(self, length=10) -> str:
        chars = string.ascii_letters + string.digits
        while True:
            token = "".join(random.choices(chars, k=length))
            if not Link.objects.filter(token=token).exists():
                return token

    def get_permalink(self):
        return f"{get_host()}/t/{self.token}"

    def self_test(self):
        target_url = self.share.target_url if self.share else self.direct_target_url
        try:
            response = requests.get(target_url, timeout=5)
            print(response)
            if response.status_code < 400:
                return True
            return False
        except Exception as e:
            print(e)
            return False


@receiver(post_delete, sender=Link)
def delete_associated_share(sender, instance, **kwargs):
    share = instance.share
    if share:
        share.delete()
