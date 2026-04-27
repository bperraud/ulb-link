from django.shortcuts import get_object_or_404
from django.conf import settings
from link.auth import get_valid_access_token
import requests, json
from link.models import Link, User, Share

# import xml.etree.ElementTree as ET
from xml.etree import ElementTree as ET
from urllib.parse import unquote


class NextcloudError(Exception):
    pass


class NotAuthenticated(Exception):
    pass


def is_folder(resp, ns):
    resourcetype = resp.find("d:propstat/d:prop/d:resourcetype", ns)
    if resourcetype is not None:
        return resourcetype.find("d:collection", ns) is not None
    return False


def webdav_to_jstree(xml, user: User):
    ns = {"d": "DAV:"}
    root = ET.fromstring(xml)
    base = f"/remote.php/dav/files/{user.username}/"
    nodes = []

    paths = Link.objects.filter(user=user, share__isnull=False).values_list(
        "share__path", flat=True
    )

    for resp in root.findall("d:response", ns):
        href_el = resp.find("d:href", ns)
        if href_el is None:
            continue

        href = href_el.text
        # Extract relative path
        if not href.startswith(base):
            continue

        rel_path = href[len(base) :]  # remove prefix
        rel_path = unquote(rel_path).rstrip("/")

        folder = is_folder(resp, ns)

        # Root folder
        if rel_path == "":
            path = "/"
            name = user.username
            parent = "#"
        else:
            path = "/" + rel_path
            name = rel_path.split("/")[-1]

            # Compute parent correctly
            parent_path = "/" + rel_path.rsplit("/", 1)[0] if "/" in rel_path else "/"
            parent = parent_path

        if path not in paths or folder:
            nodes.append(
                {
                    "id": path,
                    "parent": parent,
                    "text": name,
                    "icon": "jstree-folder" if folder else "jstree-file",
                }
            )

    return {"data": nodes}


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
    headers = {"Authorization": f"Bearer {access_token}", "OCS-APIRequest": "true"}
    try:
        response = requests.put(
            f"{settings.NEXTCLOUD_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares/{id}",
            headers=headers,
            data=data,
        )
        print(response)
    except:
        raise NextcloudError("Error reaching Nextcloud Api")

    if response.status_code != 200:
        raise NextcloudError(
            "Error reaching Nextcloud Api " + str(response.status_code)
        )


def create_share_in_nextcloud(request, path):
    access_token = get_valid_access_token(request)
    if not access_token:
        raise NotAuthenticated()

    data = {"path": path, "shareType": 3, "permissions": 1}
    headers = {"Authorization": f"Bearer {access_token}", "OCS-APIRequest": "true"}

    try:
        response = requests.post(
            f"{settings.NEXTCLOUD_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares",
            headers=headers,
            data=data,
        )
    except:
        raise NextcloudError("Error reaching Nextcloud Api")

    if response.status_code > 300:
        raise NextcloudError(
            "Error reaching Nextcloud Api " + str(response.status_code)
        )

    root = ET.fromstring(response.text)

    share_id = root.find("./data/id").text
    url = root.find("./data/url").text
    return share_id, url


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

    return json.loads(response.text)


def get_nextcloud_files(request):
    access_token = get_valid_access_token(request)
    if not access_token:
        raise NotAuthenticated()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Depth": "infinity",
        "Content-Type": "application/xml",
    }

    xml_body = """<?xml version="1.0"?>
    <d:propfind xmlns:d="DAV:">
      <d:prop>
        <d:getlastmodified/>
        <d:getcontentlength/>
        <d:resourcetype/>
      </d:prop>
    </d:propfind>
    """
    try:
        response = requests.request(
            headers=headers,
            method="PROPFIND",
            url=f"{settings.NEXTCLOUD_URL}/remote.php/dav/files/{request.user.username}",
            data=xml_body,
        )
    except:
        raise NextcloudError("Error reaching Nextcloud Api")
    if response.status_code > 300:
        raise NextcloudError("Error reaching Nextcloud Api")

    return response.content
