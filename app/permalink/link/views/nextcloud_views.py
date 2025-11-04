from django.shortcuts import get_object_or_404, redirect
from link.auth import get_valid_access_token
from django.http import HttpResponse
import requests

from link.models import Share

import xml.etree.ElementTree as ET
from django.conf import settings

def parse_xml(xml_data: str):
    root = ET.fromstring(xml_data)
    # namespace handling is not required here as the XML has no default NS
    elements = root.find("data").findall("element")

    for el in elements:
        try :
            share = Share.objects.get(uid=el.findtext("id"))
            share.path = el.findtext("path")
            index = share.target_url.rfind('/')
            share.target_url = share.target_url[:index + 1] + el.findtext("token")
            share.expiration = el.findtext("expiration") if el.findtext("expiration") else None
            share.save()
        except Share.DoesNotExist:
            pass

def update_share_in_nextcloud(request, id):
    access_token = get_valid_access_token(request)
    if not access_token:
        return redirect("login")

    share = get_object_or_404(Share, uid=id)
    if (not share.expiration):
         return HttpResponse(200)

    data = {
        "expireDate": share.expiration.strftime('%Y-%m-%d')
    }
    # use the token to make an API call
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.put(
        f"{settings.NEXTCLOUD_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares/{id}",
        headers=headers,
        data=data,
    )
    return HttpResponse(response.text,status=response.status_code)

def update_shares_object(request):
    access_token = get_valid_access_token(request)
    if not access_token:
        return redirect("login")

    # use the token to make an API call
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{settings.NEXTCLOUD_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares",
        headers=headers,
    )

    if (response.status_code == 200):
        parse_xml(response.text)

    return HttpResponse(response.text)
