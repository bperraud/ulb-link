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

    is_valid = models.BooleanField(default=True)

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

    def self_test(self) -> bool:
        target_url = getattr(self.share, "target_url", None) or self.direct_target_url

        if not target_url:
            self.is_valid = False
            self.save(update_fields=["is_valid"])
            return False

        try:
            response = requests.get(target_url, timeout=5)
            is_valid = response.status_code < 400

        except Exception as e:
            is_valid = False

        self.is_valid = is_valid
        self.save(update_fields=["is_valid"])

        return is_valid


@receiver(post_delete, sender=Link)
def delete_associated_share(sender, instance, **kwargs):
    share = instance.share
    if not share:
        return

    still_used = Link.objects.filter(share=share).exists()
    if not still_used:
        share.delete()
