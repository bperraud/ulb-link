from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator

from link.context_processors import get_host
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Share(models.Model):
    uid = models.IntegerField(primary_key=True)
    target_url = models.URLField(verbose_name="Target URL")
    path = models.CharField()
    expiration = models.DateTimeField(null=True)


class Link(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="link")
    share = models.ForeignKey(Share, on_delete=models.DO_NOTHING, related_name="share")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    token = models.CharField(
        validators=[MinLengthValidator(8)],
        max_length=20,
        verbose_name="Token",
        unique=True,
        null=False,
    )

    def get_permalink(self):
        return f"{get_host()}/{self.token}"


@receiver(post_delete, sender=Link)
def delete_associated_share(sender, instance, **kwargs):
    share = instance.share
    if share:
        share.delete()
