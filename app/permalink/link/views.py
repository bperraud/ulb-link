from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import TemplateView, DetailView, ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from link.models import Link, User


@method_decorator([login_required], name="dispatch")
class LinkListView(ListView):
    model = Link
    template_name = "home.html"
    context_object_name = "links"

    def get_queryset(self):
        query = Link.objects.filter(user=self.request.user)
        print(query)
        return query
