from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from rest_framework.generics import get_object_or_404
from link.decorators import nextcloud_user_required
from link.models import Link
from link.forms import LinkForm
from link.views.nextcloud_views import update_shares_object, update_share_in_nextcloud


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
            if link.share:
                update_share_in_nextcloud(request, link.share.uid)
                response["HX-Redirect"] = reverse("mycloud-link")
            else:
                response["HX-Redirect"] = reverse("link-home")
            return response
    else:
        form = LinkForm(instance=link)

    return render(request, "modal.html", {"form": form, "link": link})

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
            response["HX-Redirect"] = reverse("link-home")
            return response

    return render(request, "modal_create.html", {"form": form})

def targetURL(token):
    link = get_object_or_404(Link, token=token)
    return redirect(link.share.target_url)

def status():
    return JsonResponse({"message": "ok"})
