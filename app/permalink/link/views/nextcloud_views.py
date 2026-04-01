from django.shortcuts import get_object_or_404, redirect
from link.auth import get_valid_access_token
from django.http import HttpResponse
import requests, json

from link.models import Share

from django.conf import settings


class NextcloudError(Exception):
    pass


def parse_json(json_data: dict):
    for el in json_data["ocs"]["data"]:
        try:
            share = Share.objects.get(uid=el.get("id"))
            share.path = el.get("path")
            index = share.target_url.rfind("/")
            share.target_url = share.target_url[: index + 1] + el.get("token")
            share.expiration = el.get("expiration") if el.get("expiration") else None
            share.save()
        except Share.DoesNotExist:
            pass


def update_share_in_nextcloud(request, id):
    access_token = get_valid_access_token(request)
    if not access_token:
        return redirect("login")

    share = get_object_or_404(Share, uid=id)
    if not share.expiration:
        raise NextcloudError("Share does not have an expiration date")

    data = {"expireDate": share.expiration.strftime("%Y-%m-%d")}
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.put(
            f"{settings.NEXTCLOUD_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares/{id}",
            headers=headers,
            data=data,
        )
    except:
        raise NextcloudError("Error reaching Nextcloud Api")

    if response.status_code != 200:
        raise NextcloudError("Error reaching Nextcloud Api")


def update_shares_object(request):
    shares = get_nextcloud_shares(request)
    parse_json(shares)


def get_nextcloud_shares(request) -> dict:
    access_token = get_valid_access_token(request)
    if not access_token:
        return redirect("login")

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(
            f"{settings.NEXTCLOUD_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json",
            headers=headers,
        )
    except:
        raise NextcloudError("Error reaching Nextcloud Api")

    if response.status_code != 200:
        raise NextcloudError("Error reaching Nextcloud Api")

    return json.loads(response.text)
