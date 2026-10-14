from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from authlib.integrations.django_client import OAuth
from authlib.integrations.requests_client import OAuth2Session

from django.conf import settings

from link.models import User
import jwt, time, requests, logging

logger = logging.getLogger(__name__)


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

        username = payload.get("sub")

        if username == "anonymous-nextcloud-user":
            return (None, None)

        user, _ = User.objects.get_or_create(username=payload.get("sub"))
        # user, _ = User.objects.get_or_create(username=payload.get("sub"))
        return (user, None)


oauth = OAuth()
oauth.register(name="nextcloud", **settings.AUTHLIB_OAUTH_CLIENTS)


def get_access_token(request):
    token = request.user.oauth_token
    if not token:
        return None  # Not authenticated

    now = int(time.time())
    if now >= int(token["expires_at"]) - 60:  # refresh 1 min before expiry
        token = refresh_token(token)
        if not token:
            return None
        request.user.oauth_token = token
        request.user.save(update_fields=["oauth_token"])

    return token["access_token"]


def refresh_token(token):
    client = OAuth2Session(
        settings.AUTHLIB_OAUTH_CLIENTS["client_id"],
        settings.AUTHLIB_OAUTH_CLIENTS["client_secret"],
        token=token,
    )

    #     import logging
    #     logging.basicConfig(level=logging.DEBUG)
    #     logging.getLogger("authlib").setLevel(logging.DEBUG)
    #     logging.getLogger("urllib3").setLevel(logging.DEBUG)

    try:
        new_token = client.refresh_token(
            settings.AUTHLIB_OAUTH_CLIENTS["refresh_token_url"],
            refresh_token=token["refresh_token"],
        )
        return new_token
    except Exception as e:
        if hasattr(e, "response") and hasattr(e.response, "text"):
            logger.error(f"Error refresh token: {e.response.text}")
        return None


def is_nextcloud_user(uid: str) -> bool:
    headers = {"OCS-APIRequest": "true"}
    try:
        response = requests.get(
            f"{settings.NEXTCLOUD_URL}/ocs/v2.php/cloud/users/{uid}?format=json",
            auth=(settings.NEXTCLOUD_ADMIN_USER, settings.NEXTCLOUD_ADMIN_PASSWORD),
            headers=headers,
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        return data["ocs"]["meta"]["status"] == "ok"
    except requests.exceptions.RequestException:
        return False
