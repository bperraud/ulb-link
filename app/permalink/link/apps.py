from django.apps import AppConfig
from django.conf import settings
import mozilla_django_oidc.utils

class PermalinkConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "link"

def absolutify_https(request, path):
    url = request.build_absolute_uri(path)
    if settings.OIDC_FORCE_HTTPS:
        url = url.replace("http://", "https://", 1)
    return url

mozilla_django_oidc.utils.absolutify = absolutify_https
