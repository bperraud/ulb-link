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
from link.forms import LinkForm


@method_decorator([login_required], name="dispatch")
class LinkListView(ListView):
    model = Link
    template_name = "links.html"
    context_object_name = "links"

    def get_queryset(self):
        return Link.objects.filter(user=self.request.user)


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
            return response
    else:
        form = LinkForm(instance=link)

    return render(request, "modal.html", {"form": form, "link": link})


def targetURL(request, token):
    link = get_object_or_404(Link, token=token)
    return redirect(link.target_url)


def status(request):
    return JsonResponse({"message": "ok"})


from django.shortcuts import redirect
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.models import User

from link.auth import oauth


# 1. Redirect to Nextcloud
def login_view(request):
    redirect_uri = request.build_absolute_uri("/auth/callback/")
    return oauth.nextcloud.authorize_redirect(request, redirect_uri)


# 2. Callback URL after login
def auth_callback(request):
    token = oauth.nextcloud.authorize_access_token(request)
    if not token:
        return HttpResponse("Authorization failed", status=401)

    # You may need to query a user endpoint. Example:
    userinfo_response = oauth.nextcloud.get(
        "/ocs/v2.php/cloud/user?format=json", token=token
    )
    userinfo = userinfo_response.json()

    # Extract the username or email (depends on Nextcloud config)
    cloud_user = userinfo.get("ocs", {}).get("data", {})
    username = cloud_user.get("id")
    email = cloud_user.get("email") or f"{username}@nextcloud.local"

    # Django login or create
    user, _ = User.objects.get_or_create(username=username, defaults={"email": email})
    login(request, user)

    return redirect("/")  # Redirect to home or dashboard
