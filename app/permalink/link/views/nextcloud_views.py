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
from link.models import NextcloudShareBatchJob, Link, Share
from link.views.nextcloud_utils import (
    webdav_to_jstree,
    mycloud_api,
)

from permalink.tasks import sync_user_shares

from datetime import timedelta
from django.utils import timezone


def should_sync(user):
    if user.last_share_sync is None:
        return True
    return timezone.now() - user.last_share_sync > timedelta(hours=1)


@method_decorator([nextcloud_connected_user_required, login_required], name="dispatch")
class MycloudLinkTableView(ListView):
    model = Link
    context_object_name = "links"
    template_name = "mycloud/mycloud_link_table.html"

    def get_queryset(self):
        if should_sync(self.request.user):
            response = mycloud_api.get_shares(self.request)
            sync_user_shares.delay(response.json())
            self.request.user.last_share_sync = timezone.now()
            self.request.user.save()
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
def create_nextcloud_bulk(request):
    response = HttpResponse()
    response["HX-Refresh"] = "true"

    try:
        response_xml = mycloud_api.get_files(request)  # can throw error
        tree_data = webdav_to_jstree(response_xml, request.user)
    except Exception as e:
        response["HX-Trigger"] = json.dumps(
            {
                "flashMessage": "Error while creating permalink : " + str(e),
                "type": "error",
            }
        )
        return response

    if request.method == "POST":
        selected_path = request.POST.get("selected_nodes")
        selected_files = json.loads(selected_path)
        file_paths = []
        for file in selected_files:
            if file["icon"] == "jstree-folder":
                continue
            file_paths.append(file["id"])
        job = NextcloudShareBatchJob.objects.filter(user=request.user).first()

        if job:
            job.file_paths += file_paths
            job.initial_file_count += len(file_paths)
            job.oauth_token = request.session["oauth_token"]
            job.save()
        else:
            NextcloudShareBatchJob.objects.create(
                user=request.user,
                oauth_token=request.session["oauth_token"],
                file_paths=file_paths,
                initial_file_count=len(file_paths),
            )
        response["HX-Trigger"] = json.dumps(
            {
                "flashMessage": "Permalink creation has started and will continue in the background (up to 100 every 10 minutes)."
            }
        )
        return response

    tree_data["modal_title"] = "Create permalinks for selected files"
    return render(
        request,
        "modals/modal_create_nextcloud_bulk.html",
        tree_data,
    )


# Deprecated
@login_required
@nextcloud_connected_user_required
@require_http_methods(["GET", "POST"])
def create_bulk(request):
    response = mycloud_api.get_shares(request)
    json_shares = response.json()
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
@require_http_methods(["GET"])
def bulk_task_advancement(request):
    task = NextcloudShareBatchJob.objects.filter(user=request.user).first()

    file_count_left = task.initial_file_count - len(task.file_paths)
    pct = min(100, round(file_count_left / task.initial_file_count * 100))
    if task:

        return render(
            request,
            "mycloud/bulk_task_advancement.html",
            {
                "file_count_left": len(task.file_paths),
                "initial_file_count": task.initial_file_count,
                "pct": pct,
            },
        )
    return HttpResponse()
