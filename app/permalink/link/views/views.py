from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from rest_framework.generics import get_object_or_404
from link.models import Link
from link.views.nextcloud_views import update_shares_object
from link.forms import LinkForm
from link.views.nextcloud_views import update_share_in_nextcloud 


@method_decorator([login_required], name="dispatch")
class LinkTableView(ListView):
    model = Link
    context_object_name = "links"

    def get_template_names(self):
        user = self.request.user
        print(user.is_nextcloud_user)
        if getattr(user, "is_nextcloud_user", True):
            return ["mycloud/mycloud_link_table.html"]
        else:
            return ["link_table.html"]

    def get_queryset(self):
        if getattr(self.request.user, "is_nextcloud_user", True):
            update_shares_object(self.request)
        print(Link.objects.filter(user=self.request.user))
        return Link.objects.filter(user=self.request.user)

@method_decorator([login_required], name="dispatch")
class MycloudLinkTableView(ListView):
    model = Link
    context_object_name = "links"

    def get_template_names(self):
        user = self.request.user
        print(user.is_nextcloud_user)
        if getattr(user, "is_nextcloud_user", True):
            return ["mycloud/mycloud_link_table.html"]

    def get_queryset(self):
        if getattr(self.request.user, "is_nextcloud_user", True):
            update_shares_object(self.request)
        print(Link.objects.filter(user=self.request.user))
        return Link.objects.filter(user=self.request.user)

@method_decorator([login_required], name="dispatch")
class LinkRowView(TemplateView):
    def get_template_names(self):
        user = self.request.user
        print(user.is_nextcloud_user)
        if getattr(user, "is_nextcloud_user", True):
            return ["mycloud/mycloud_link_row.html"]
        else:
            return ["link_row.html"]
    # template_name = "mycloud_links_table.html"

    def get_context_data(self, **kwargs):
        link = get_object_or_404(Link, pk=kwargs["pk"])
        return {"link": link}


@require_http_methods(["GET"])
def toolbar(request, nb):
    match nb:
        case 0:
            return HttpResponse("")
        case 1:
            return render(request, "link_bar/edit_single_link.html")
        case _:
            return render(request, "link_bar/edit_multiple_link.html")


@require_http_methods(["DELETE"])
def delete_links(request, ids):
    list_ids = ids.split(",")
    links = Link.objects.filter(id__in=(list_ids))
    links.delete()
    return JsonResponse({"message": "ok"})


@require_http_methods(["GET", "POST"])
def edit_link(request, pk):
    link = get_object_or_404(Link, pk=pk)
    if request.method == "POST":
        form = LinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            response = HttpResponse()
            response["HX-Redirect"] = reverse("link-home")
            update_share_in_nextcloud(request, link.share.uid)
            return response
    else:
        form = LinkForm(instance=link)

    return render(request, "modal.html", {"form": form, "link": link})


def targetURL(request, token):
    link = get_object_or_404(Link, token=token)
    return redirect(link.share.target_url)


def status(request):
    return JsonResponse({"message": "ok"})
