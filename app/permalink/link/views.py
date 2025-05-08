from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, DetailView, ListView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from rest_framework.generics import get_object_or_404
from link.models import Link, User


@method_decorator([login_required], name="dispatch")
class LinkListView(ListView):
    model = Link
    template_name = "links.html"
    context_object_name = "links"

    def get_queryset(self):
        return Link.objects.filter(user=self.request.user)


@method_decorator([login_required], name="dispatch")
class LinkEditRowView(TemplateView):
    template_name = "edit_row.html"

    def get_context_data(self, **kwargs):
        link = get_object_or_404(Link, pk=kwargs["pk"])
        return {"link": link}


@method_decorator([login_required], name="dispatch")
class LinkRowView(TemplateView):
    template_name = "link_row.html"

    def get_context_data(self, **kwargs):
        link = get_object_or_404(Link, pk=kwargs["pk"])
        return {"link": link}


def targetURL(request, token):
    link = get_object_or_404(Link, token=token)
    return redirect(link.target_url)
