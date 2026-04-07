from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import login, logout
from link.auth import oauth
from django.conf import settings
import urllib.parse

from link.context_processors import get_host
from link.models import User


def login_view(request):
    return render(request, "login_page.html")


def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect(
        f"{settings.OIDC_OP_LOGOUT_ENDPOINT}?service={urllib.parse.quote(get_host(), safe='')}"
    )


def mycloud_login_view(request):
    redirect_uri = request.build_absolute_uri("/auth/callback/")
    response = oauth.nextcloud.authorize_redirect(request, redirect_uri)
    # request.session.save()  # ensure the session with state is persisted
    return response


def auth_callback(request):

    print(request.is_secure())

    token = oauth.nextcloud.authorize_access_token(request)
    if not token:
        return HttpResponse("Authorization failed", status=401)

    userinfo_response = oauth.nextcloud.get(
        "/ocs/v2.php/cloud/user?format=json", token=token
    )
    userinfo = userinfo_response.json()
    # Extract the username or email (depends on Nextcloud config)
    cloud_user = userinfo.get("ocs", {}).get("data", {})
    username = cloud_user.get("id")
    email = cloud_user.get("email") or f"{username}@nextcloud.be"

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create(username=username, email=email)

    user.is_nextcloud_user = True
    user.save()

    login(request, user, backend=settings.AUTHENTICATION_BACKENDS[1])
    request.session["oauth_token"] = token

    return redirect("/")
