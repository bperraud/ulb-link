from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import auth

from link.models import User

from mycloud.auth import is_nextcloud_user


class OIDCCAS(OIDCAuthenticationBackend):

    def verify_claims(self, claims):
        return True

    def filter_users_by_claims(self, claims):
        username = claims.get("id", "")
        if not username:
            username = claims.get("sub", "")
        return User.objects.filter(username=username)

    def save_fields(self, user, claims):
        user.username = claims.get("id", "")
        user.email = claims.get("email", "")
        user.save()

    def create_user(self, claims):
        user = super(OIDCCAS, self).create_user(claims)
        self.save_fields(user, claims)
        return user

    def update_user(self, user, claims):
        self.save_fields(user, claims)
        return user


class OIDCCallbackView(OIDCAuthenticationCallbackView):
    def login_success(self):
        request_user = getattr(self.request, "user", None)
        if (
            not request_user
            or not request_user.is_authenticated
            or request_user != self.user
        ):
            auth.login(self.request, self.user)
        if is_nextcloud_user(self.request.user.get_username()):
            return redirect(reverse("mycloud_login"))
        return super().login_success()
