from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
import jwt
from authlib.integrations.django_client import OAuth
from authlib.integrations.requests_client import OAuth2Session

from datetime import datetime, timedelta
from django.utils import timezone

from django.contrib.auth.models import User

from django.conf import settings

User = get_user_model()


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
oauth.register(name="nextcloud", **settings.AUTHLIB_OAUTH_CLIENTS["nextcloud"])


def get_valid_access_token(request):
    token = request.session.get("oauth_token")
    if not token:
        return None  # Not authenticated

    expires_at = datetime.fromisoformat(token["expires_at"])
    now = timezone.now()

    if now >= expires_at - timedelta(minutes=1):  # refresh 1 min before expiry
        token = refresh_token(token["refresh_token"])
        if not token:
            return None
        request.session["oauth_token"] = token

    return token["access_token"]


def refresh_token(refresh_token):
    client = OAuth2Session(
        client_id=settings.AUTHLIB_OAUTH_CLIENTS["client_id"],
        client_secret=settings.AUTHLIB_OAUTH_CLIENTS["client_secret"],
    )

    try:
        token = client.refresh_token(
            url=settings.AUTHLIB_OAUTH_CLIENTS["refresh_token"],
            refresh_token=refresh_token,
        )

        return {
            "access_token": token["access_token"],
            "refresh_token": token.get("refresh_token", refresh_token),
            "expires_at": (
                timezone.now() + timedelta(seconds=token["expires_in"])
            ).isoformat(),
        }

    except Exception as e:
        print(f"Token refresh failed: {e}")
        return None
