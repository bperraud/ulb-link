from django.http import HttpResponseForbidden
from functools import wraps
from django.conf import settings
from link.auth import get_valid_access_token
from django.shortcuts import redirect
from django.urls import reverse


def nextcloud_user_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        access_token = get_valid_access_token(request)
        if not access_token:
            return redirect(reverse("mycloud_login"))
        if settings.DEBUG == True:
            return view_func(request, *args, **kwargs)
        if getattr(request.user, "is_nextcloud_user", True):
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden(
            b"You need to log with nextcloud to view this page."
        )

    return _wrapped_view
