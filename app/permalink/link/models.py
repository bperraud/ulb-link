from django.db import models
from django.contrib.auth.models import User

from link.context_processors import get_host


class Link(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="link")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    target_url = models.URLField(verbose_name="Target URL")
    token = models.CharField(max_length=50, verbose_name="Token", unique=True)

    class Meta:
        unique_together = ("user", "token")

    def get_permalink(self):
        return f"{get_host()}/{self.token}"
