from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from permalink.utils import *

import json
from rest_framework.generics import get_object_or_404
from link.models import Link, User
from link.forms import LinkForm
from link.views.nextcloud_utils import (
    mycloud_api,
)


@method_decorator([login_required], name="dispatch")
class LinkTableView(ListView):
    model = Link
    context_object_name = "links"
    template_name = "link_table.html"

    def get_queryset(self):
        return Link.objects.filter(user=self.request.user, share=None)


@method_decorator([login_required], name="dispatch")
class LinkRowView(TemplateView):
    template_name = "link_row.html"

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
                    mycloud_api.update_share(request, link.share.uid)
                except Exception as e:
                    response["HX-Trigger"] = json.dumps(
                        {
                            "flashMessage": "Error editing Permalink : " + str(e),
                            "type": "error",
                        }
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


def redirect_with_suffix(request, token, suffix):
    link = get_object_or_404(Link, token=token)
    targetURL = link.share.target_url if link.share else link.direct_target_url
    return redirect(targetURL + f"/{suffix}")


def status(request):
    return JsonResponse({"message": "ok"})


def unsubscribe_email(request, token):
    if request.method == "POST":
        payload = verify_token(token)
        if payload:
            user = User.objects.get(id=payload)
            user.unsubscribe_from_email = True
            user.save()
            return render(request, "email/unsubscribe_success.html")
        return HttpResponse("Error unsubscribe from email")

    return render(request, "email/unsubscribe_from_email.html", {"token": token})
