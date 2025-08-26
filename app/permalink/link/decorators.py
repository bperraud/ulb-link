from django.http import HttpResponseForbidden
from functools import wraps

def nextcloud_user_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if getattr(request.user, "is_nextcloud_user", True):
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You need to log with nextcloud to view this page.")
    return _wrapped_view

