from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import login
from link.auth import oauth

from link.models import User

from django.contrib.auth.models import User

def login_view(request):
    return render(request, 'login_page.html')
    # redirect_uri = request.build_absolute_uri("/auth/callback/")
    # response = oauth.nextcloud.authorize_redirect(request, redirect_uri)
    # request.session.save()  # ensure the session with state is persisted
    # return response

# def login_view(request):
#     redirect_uri = request.build_absolute_uri("/auth/callback/")
#     response = oauth.nextcloud.authorize_redirect(request, redirect_uri)
#     request.session.save()  # ensure the session with state is persisted
#     return response

def auth_callback(request):
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
    email = cloud_user.get("email") or f"{username}@nextcloud.local"
    user, _ = User.objects.get_or_create(username=username, defaults={"email": email})

    login(request, user)
    request.session["oauth_token"] = token
    return redirect("/")
