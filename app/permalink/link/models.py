from enum import unique
from django.db import models
from django.contrib.auth.models import User


class Link(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="link")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    target_url = models.URLField(verbose_name="Target URL")
    token = models.CharField(max_length=50, verbose_name="Token", unique=True)
