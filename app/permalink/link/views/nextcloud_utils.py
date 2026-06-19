from django.shortcuts import get_object_or_404
from django.conf import settings
from link.auth import get_access_token
from link.models import Link, NextcloudShareBatchJob, User, Share

from xml.etree import ElementTree as ET
from urllib.parse import unquote
import requests


class NextcloudError(Exception):
    pass


class NotAuthenticated(Exception):
    pass


def webdav_to_jstree(xml, user: User):

    def is_folder(resp, ns):
        resourcetype = resp.find("d:propstat/d:prop/d:resourcetype", ns)
        if resourcetype is not None:
            return resourcetype.find("d:collection", ns) is not None
        return False

    ns = {"d": "DAV:"}
    root = ET.fromstring(xml)
    base = f"/remote.php/dav/files/{user.username}/"
    nodes = []
    job = NextcloudShareBatchJob.objects.filter(user=user).first()
    paths = list(
        Link.objects.filter(
            user=user,
            share__isnull=False,
        ).values_list("share__path", flat=True)
    ) + (job.file_paths if job else [])

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


def update_shares_object(response):
    for el in response["ocs"]["data"]:
        try:
            share = Share.objects.get(uid=el.get("id"))
        except Share.DoesNotExist:
            continue
        share.path = el.get("path")
        index = share.target_url.rfind("/")
        share.target_url = share.target_url[: index + 1] + el.get("token")
        share.expiration = el.get("expiration") if el.get("expiration") else None
        share.save()


# Deprecated
def get_or_create_share_in_nextcloud(request, path):
    response = mycloud_api.get_share(request, path)
    share_data = response.json()["ocs"]["data"]
    share_exist = False

    if share_data:  # share exist -> need to parse all shares
        for share in share_data:
            if share["share_type"] == 3:
                share_data = share
                share_exist = True
                break

    if not share_exist:
        response = mycloud_api.create_share(request, path)
        share_data = response.json()["ocs"]["data"]

    share, _ = Share.objects.get_or_create(
        uid=share_data["id"],
        path=share_data["path"],
        target_url=share_data["url"],
    )
    return share


def get_or_create_share(request, path):
    response = mycloud_api.get_share(request, path)
    share_data = response.json()["ocs"]["data"]
    share_exist = False

    if share_data:  # share exist -> need to parse all shares
        for share in share_data:
            if share["share_type"] == 3:
                share_data = share
                share_exist = True
                break

    if not share_exist:
        response = mycloud_api.create_share(request, path)
        share_data = response.json()["ocs"]["data"]

    share, _ = Share.objects.get_or_create(
        uid=share_data["id"],
        path=share_data["path"],
        target_url=share_data["url"],
    )
    return share


class MycloudAPI:

    def __init__(self, url, timeout, debug):
        self.url = url
        self.timeout = timeout
        self.debug = debug

    def _get_access_token(self, request) -> str:
        access_token = get_access_token(request)
        if not access_token:
            raise NotAuthenticated()
        return access_token

    def _get_ocs_headers(self, request) -> dict:
        return {
            "Authorization": f"Bearer {self._get_access_token(request)}",
            "OCS-APIRequest": "true",
        }

    def _get_webdav_headers(self, request) -> dict:
        return {
            "Authorization": f"Bearer {self._get_access_token(request)}",
            "Depth": "infinity",
            "Content-Type": "application/xml",
        }

    def _request(
        self,
        method: str,
        api_path: str,
        params: dict | None = None,
        data=None,
        headers: dict | None = None,
        timeout: int | float | tuple | None = None,
    ) -> requests.Response:

        url = f"{self.url}{api_path}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                timeout=timeout if timeout is not None else self.timeout,
            )

        except requests.Timeout as exc:
            raise NextcloudError("Nextcloud request timed out") from exc

        except requests.RequestException as exc:
            raise NextcloudError("Error reaching Nextcloud API") from exc

        if response.status_code == 429:
            raise NextcloudError(
                "Too many requests: maximum 100 shares every 10 minutes."
            )

        if response.status_code >= 300:
            raise NextcloudError(f"Nextcloud API returned HTTP {response.status_code}")

        return response

    #
    # OCS API
    #
    def get_share(self, request, path: str) -> requests.Response:
        return self._request(
            method="GET",
            api_path="/ocs/v2.php/apps/files_sharing/api/v1/shares",
            params={
                "format": "json",
                "path": path,
            },
            headers=self._get_ocs_headers(request),
        )

    def get_shares(self, request) -> requests.Response:
        return self._request(
            method="GET",
            api_path="/ocs/v2.php/apps/files_sharing/api/v1/shares",
            params={"format": "json"},
            headers=self._get_ocs_headers(request),
            timeout=180,
        )

    def create_share(self, request, path: str) -> requests.Response:
        return self._request(
            method="POST",
            api_path="/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json",
            data={
                "path": path,
                "shareType": 3,
                "permissions": 1,
            },
            headers=self._get_ocs_headers(request),
        )

    def update_share(self, request, share_id: int) -> requests.Response:
        share = get_object_or_404(Share, uid=share_id)

        if not share.expiration:
            raise NextcloudError("Share does not have an expiration date")

        return self._request(
            method="PUT",
            api_path=f"/ocs/v2.php/apps/files_sharing/api/v1/shares/{share_id}",
            data={
                "expireDate": share.expiration.strftime("%Y-%m-%d"),
            },
            headers=self._get_ocs_headers(request),
        )

    def get_files(self, request) -> bytes:
        xml_body = """<?xml version="1.0"?>
        <d:propfind xmlns:d="DAV:">
          <d:prop>
            <d:getlastmodified/>
            <d:getcontentlength/>
            <d:resourcetype/>
          </d:prop>
        </d:propfind>
        """

        response = self._request(
            method="PROPFIND",
            api_path=f"/remote.php/dav/files/{request.user.username}",
            data=xml_body,
            headers=self._get_webdav_headers(request),
        )

        return response.content


mycloud_api = MycloudAPI(url=settings.NEXTCLOUD_URL, timeout=30, debug=False)
