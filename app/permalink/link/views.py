from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import FormView

from django.views.decorators.http import require_http_methods
from django.urls import reverse_lazy

from rest_framework.generics import get_object_or_404
from link.models import Link

from django.http import JsonResponse, HttpResponse

from link.forms import LinkForm
from django.urls import reverse
from django.template.loader import render_to_string


@method_decorator([login_required], name="dispatch")
class LinkListView(ListView):
    model = Link
    template_name = "links.html"
    context_object_name = "links"

    def get_queryset(self):
        return Link.objects.filter(user=self.request.user)


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

    return render(request, "modal.html", {"form": form})


@method_decorator([login_required], name="dispatch")
class LinkRowView(TemplateView):
    template_name = "link_row.html"

    def get_context_data(self, **kwargs):
        link = get_object_or_404(Link, pk=kwargs["pk"])
        return {"link": link}


def targetURL(request, token):
    link = get_object_or_404(Link, token=token)
    return redirect(link.target_url)
