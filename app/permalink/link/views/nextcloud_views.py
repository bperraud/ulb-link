from django.shortcuts import get_object_or_404
from django.conf import settings
from link.auth import get_valid_access_token
import requests, json

from link.models import Share


class NextcloudError(Exception):
    pass


class NotAuthenticated(Exception):
    pass


def parse_json(json_data: dict):
    for el in json_data["ocs"]["data"]:
        try:
            share = Share.objects.get(uid=el.get("id"))
            share.path = el.get("file_target")
            index = share.target_url.rfind("/")
            share.target_url = share.target_url[: index + 1] + el.get("token")
            share.expiration = el.get("expiration") if el.get("expiration") else None
            share.save()
        except Share.DoesNotExist:
            pass


def update_share_in_nextcloud(request, id):
    access_token = get_valid_access_token(request)
    if not access_token:
        raise NotAuthenticated()

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
        raise NotAuthenticated()

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

    print("nextcloud shares")
    print(json.loads(response.text))

    return json.loads(response.text)
