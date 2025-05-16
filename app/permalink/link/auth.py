from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.contrib.auth import get_user_model
import jwt

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
            user = User.objects.get(email=payload.get("sub"))
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")

        return (user, None)


from authlib.integrations.django_client import OAuth


oauth = OAuth()
