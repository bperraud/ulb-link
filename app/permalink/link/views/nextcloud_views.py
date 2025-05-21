from django.shortcuts import get_object_or_404, render, redirect
from link.auth import get_valid_access_token
from django.http import HttpResponse, JsonResponse
import requests

from link.models import Share

import xml.etree.ElementTree as ET

def parse_xml(xml_data: str):
    root = ET.fromstring(xml_data)

    # Namespace handling is not required here as the XML has no default NS
    elements = root.find("data").findall("element")

    for el in elements:
        id = el.findtext("id")
        try :
            share = Share.objects.get(uid=el.findtext("id"))
            print(share)
            share.path = el.findtext("path")
            share.expiration = el.findtext("expiration") if el.findtext("expiration") else None
            share.save()
        except Share.DoesNotExist:
            print(f"share {id} not found")
            pass

def update_share_in_nextcloud(request, id):

    access_token = get_valid_access_token(request)

    if not access_token:
        return redirect("login")  # or raise 403

    # share = get_object_or_404(Share, uid=id)

    data = {
        "expireDate": '2026-01-01'
    }

    # Use the token to make an API call
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.put(
        "http://nextcloud.local/ocs/v2.php/apps/files_sharing/api/v1/shares/{share.uid}",
        headers=headers,
        data=data,
    )

    return HttpResponse(response.text,status=response.status_code)

def update_shares_object(request):

    access_token = get_valid_access_token(request)

    if not access_token:
        return redirect("login")  # or raise 403

    # Use the token to make an API call
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        "http://nextcloud.local/ocs/v2.php/apps/files_sharing/api/v1/shares",
        headers=headers,
    )

    if (response.status_code == 200):
        parse_xml(response.text)

    return HttpResponse(response.text)
