from django.shortcuts import render, redirect
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
        try :
            share = Share.objects.get(uid=el.findtext("id"))
            share.path = el.findtext("path")
            share.expiration = el.findtext("expiration")
            share.save()
        except Share.DoesNotExist:
            pass

        share = {
            "id": el.findtext("id"),
            "path": el.findtext("path"),
            "url": el.findtext("url"),
            "token": el.findtext("token"),
            "item_type": el.findtext("item_type"),
            "mimetype": el.findtext("mimetype"),
            "item_size": int(el.findtext("item_size")),
        }
        shares.append(share)

    for s in shares:
        print(f"{s['item_type'].capitalize()} {s['path']} → {s['url']}")


def nextcloud_api(request):

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
