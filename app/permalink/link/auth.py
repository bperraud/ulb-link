from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from authlib.integrations.django_client import OAuth
from authlib.integrations.requests_client import OAuth2Session
from django.conf import settings
from link.models import User

import jwt
import time

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None  # Returning None lets DRF fall back to other auth classes

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("JWT token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid JWT token")

        try:
            user = User.objects.get(username=payload.get("sub"))
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")

        return (user, None)


oauth = OAuth()
oauth.register(name="nextcloud", **settings.AUTHLIB_OAUTH_CLIENTS)


def get_valid_access_token(request):
    token = request.session.get("oauth_token")
    if not token:
        return None  # Not authenticated

    now = int(time.time())
    if now >= int(token["expires_at"]) - 60:  # refresh 1 min before expiry
        token = refresh_token(token)
        if not token:
            return None
        request.session["oauth_token"] = token

    return token["access_token"]


def refresh_token(refresh_token):

    client_data = {
        "client_id" : settings.AUTHLIB_OAUTH_CLIENTS["client_id"],
        "client_secret" : settings.AUTHLIB_OAUTH_CLIENTS["client_secret"] 
    }

    client = OAuth2Session(
        **client_data,
        token=refresh_token
    )

    try:
        token = client.refresh_token(
            settings.AUTHLIB_OAUTH_CLIENTS["refresh_token_url"],
            **client_data
        )
        return token

    except Exception as e:
        print(f"Token refresh failed: {e}")
        return None

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

class OIDCCAS(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(OIDCCAS, self).create_user(claims)
        user.username = claims.get('id', '')
        user.email = claims.get('email', '')
        user.is_nextcloud_user = False
        user.save()

        return user

    def update_user(self, user, claims):
        user.username = claims.get('id', '')
        user.email = claims.get('email', '')
        user.is_nextcloud_user = False
        user.save()

        return user
