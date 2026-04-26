from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from link.utils import webdav_to_jstree

import json
from rest_framework.generics import get_object_or_404
from link.decorators import nextcloud_user_required
from link.models import Link, Share
from link.forms import LinkForm
from link.views.nextcloud_views import (
    update_shares_object,
    update_share_in_nextcloud,
    get_nextcloud_shares,
    get_nextcloud_files,
    create_share_in_nextcloud,
)


@method_decorator([login_required], name="dispatch")
class LinkTableView(ListView):
    model = Link
    context_object_name = "links"
    template_name = "link_table.html"

    def get_queryset(self):
        return Link.objects.filter(user=self.request.user, share=None)


@method_decorator([nextcloud_user_required, login_required], name="dispatch")
class MycloudLinkTableView(ListView):
    model = Link
    context_object_name = "links"
    template_name = "mycloud/mycloud_link_table.html"

    def get_queryset(self):
        update_shares_object(self.request)
        return Link.objects.filter(user=self.request.user, share__isnull=False)


@method_decorator([login_required], name="dispatch")
class LinkRowView(TemplateView):
    template_name = "link_row.html"

    def get_context_data(self, **kwargs):
        link = get_object_or_404(Link, pk=kwargs["pk"])
        return {"link": link}


@method_decorator([nextcloud_user_required, login_required], name="dispatch")
class MycloudLinkRowView(TemplateView):
    template_name = "mycloud/mycloud_link_row.html"

    def get_context_data(self, **kwargs):
        link = get_object_or_404(Link, pk=kwargs["pk"])
        return {"link": link}


@require_http_methods(["GET"])
def toolbar(request, nb):
    match nb:
        case 0:
            return HttpResponse(b"")
        case 1:
            return render(request, "link_bar/edit_single_link.html")
        case _:
            return render(request, "link_bar/edit_multiple_link.html")


@login_required
@require_http_methods(["DELETE"])
def delete_links(request, ids):
    list_ids = ids.split(",")
    links = Link.objects.filter(id__in=(list_ids))
    links.delete()
    return JsonResponse({"message": "ok"})


@login_required
@require_http_methods(["GET", "POST"])
def edit_link(request, pk):
    link = get_object_or_404(Link, pk=pk)
    if request.method == "POST":
        form = LinkForm(request.POST, instance=link)
        if form.is_valid():
            response = HttpResponse()
            response["HX-Refresh"] = "true"
            if link.share:
                try:
                    update_share_in_nextcloud(request, link.share.uid)
                except Exception as e:
                    response["HX-Trigger"] = json.dumps(
                        {"flashMessage": "Error editing Permalink" + str(e)}
                    )
                    return response
            form.save()
            response["HX-Trigger"] = json.dumps(
                {"flashMessage": "Permalink successfully edited"}
            )
            return response
    else:
        form = LinkForm(instance=link)

    return render(
        request,
        "modals/modal_edit.html",
        {"form": form, "link": link, "modal_title": "Edit Permalink"},
    )


@login_required
@nextcloud_user_required
@require_http_methods(["GET", "POST"])
def create_bulk(request):
    json_shares = get_nextcloud_shares(request)
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
@nextcloud_user_required
@require_http_methods(["GET", "POST"])
def create_nextcloud_bulk(request):
    response_xml = get_nextcloud_files(request)
    tree_data = webdav_to_jstree(response_xml, request.user)

    if request.method == "POST":
        selected_path = request.POST.get("selected_nodes")
        selected_path = eval(selected_path)
        for path in selected_path:
            share_id, target_url = create_share_in_nextcloud(request, path)
            share = Share.objects.create(uid=share_id, path=path, target_url=target_url)
            Link.objects.create(user=request.user, share=share)
        response = HttpResponse()
        response["HX-Refresh"] = "true"
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


@login_required
@require_http_methods(["GET", "POST"])
def create_link(request):
    form = LinkForm()
    if request.method == "POST":
        form = LinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.user = request.user
            link.save()
            response = HttpResponse()
            response["HX-Refresh"] = "true"
            response["HX-Trigger"] = json.dumps(
                {"flashMessage": "Permalink successfully created"}
            )
            return response

    return render(
        request,
        "modals/modal_create.html",
        {"form": form, "modal_title": "Create Permalink"},
    )


def redirect_to_target_url(request, token):
    link = get_object_or_404(Link, token=token)
    targetURL = link.share.target_url if link.share else link.direct_target_url
    return redirect(targetURL)


def status(request):
    return JsonResponse({"message": "ok"})
