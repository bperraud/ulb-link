from django.shortcuts import render, redirect
from link.auth import get_valid_access_token
from django.http import HttpResponse, JsonResponse
import requests


def nextcloud_api(request):

    access_token = get_valid_access_token(request)

    print(access_token)
    if not access_token:
        return redirect("login")  # or raise 403

    # Use the token to make an API call
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        "http://nextcloud.local/ocs/v2.php/apps/files_sharing/api/v1/shares",
        headers=headers,
    )

    return HttpResponse(response.text)
