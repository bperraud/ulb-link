from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator

from link.context_processors import get_host


class Share(models.Model):
    uid = models.IntegerField(primary_key=True)
    target_url = models.URLField(verbose_name="Target URL")
    path = models.CharField()
    expiration = models.DateField(null=True)


class Link(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="link")
    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, related_name="share", null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    token = models.CharField(
        validators=[MinLengthValidator(8)],
        max_length=50,
        verbose_name="Token",
        unique=True,
    )

    class Meta:
        unique_together = ("user", "token")

    def get_permalink(self):
        return f"{get_host()}/{self.token}"
