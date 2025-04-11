from django.db import models


class Link(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="link")
    creation_date = models.DateTimeField(auto_now=True)
    target_url = models.URLField(verbose_name="Target URL")
    token = models.CharField(max_length=50, verbose_name="Token")
