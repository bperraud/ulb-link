from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

import json
from rest_framework.generics import get_object_or_404
from link.decorators import nextcloud_connected_user_required
from link.models import Link, Share
from link.views.nextcloud_utils import (
    update_shares_object,
    get_nextcloud_shares,
    get_nextcloud_files,
    get_or_create_share_in_nextcloud,
    webdav_to_jstree,
)


@method_decorator([nextcloud_connected_user_required, login_required], name="dispatch")
class MycloudLinkTableView(ListView):
    model = Link
    context_object_name = "links"
    template_name = "mycloud/mycloud_link_table.html"

    def get_queryset(self):
        try:
            update_shares_object(self.request)
        except:
            pass
        return Link.objects.filter(user=self.request.user, share__isnull=False)


@method_decorator([nextcloud_connected_user_required, login_required], name="dispatch")
class MycloudLinkRowView(TemplateView):
    template_name = "mycloud/mycloud_link_row.html"

    def get_context_data(self, **kwargs):
        link = get_object_or_404(Link, pk=kwargs["pk"])
        return {"link": link}


@login_required
@nextcloud_connected_user_required
@require_http_methods(["GET", "POST"])
def create_bulk(request):
    response = get_nextcloud_shares(request)
    json_shares = json.loads(response.text)
    shares = json_shares["ocs"]["data"]
    links = Link.objects.filter(user=request.user, share__isnull=False)

    if request.method == "POST":
        selected_ids = request.POST.getlist("share_checkbox")
        for share in shares:
            if share["id"] not in selected_ids:
                continue
            share, _ = Share.objects.get_or_create(
                uid=share["id"], target_url=share["url"]
            )
            Link.objects.create(user=request.user, share=share)
        response = HttpResponse()
        response["HX-Refresh"] = "true"
        response["HX-Trigger"] = json.dumps(
            {"flashMessage": "Permalinks successfully created"}
        )
        return response

    permalink_share_ids = [str(link.share.uid) for link in links]
    for share in shares[:]:
        if share["id"] in permalink_share_ids or share["share_type"] != 3:
            shares.remove(share)

    return render(
        request,
        "modals/modal_create_bulk.html",
        {
            "shares": shares,
            "modal_title": "Create permalinks for selected shares",
        },
    )


@login_required
@nextcloud_connected_user_required
@require_http_methods(["GET", "POST"])
def create_nextcloud_bulk(request):
    response_xml = get_nextcloud_files(request)  # can throw error
    tree_data = webdav_to_jstree(response_xml, request.user)

    if request.method == "POST":
        selected_path = request.POST.get("selected_nodes")
        selected_path = eval(selected_path)
        response = HttpResponse()
        response["HX-Refresh"] = "true"
        for path in selected_path:
            # try:
            share = get_or_create_share_in_nextcloud(request, path)
            # share = Share.objects.create(
            #     uid=share_id, path=path, target_url=target_url
            # )
            # except Exception as e:
            #     print(e)
            #     response["HX-Trigger"] = json.dumps(
            #         {
            #             "flashMessage": "Error while creating permalink : " + str(e),
            #             "type": "error",
            #         }
            #     )
            #     return response
            Link.objects.create(user=request.user, share=share)
        response["HX-Trigger"] = json.dumps(
            {"flashMessage": "Permalinks successfully created"}
        )
        return response

    tree_data["modal_title"] = "Create permalinks for selected files"
    return render(
        request,
        "modals/modal_create_nextcloud_bulk.html",
        tree_data,
    )
