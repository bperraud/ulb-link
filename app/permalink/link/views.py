from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, DetailView, ListView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import FormView

from django.urls import reverse_lazy

from rest_framework.generics import get_object_or_404
from link.models import Link, User

from django.http import HttpResponseBadRequest, JsonResponse

from link.forms import LinkForm

from django.template.loader import render_to_string


@method_decorator([login_required], name="dispatch")
class LinkListView(ListView):
    model = Link
    template_name = "links.html"
    context_object_name = "links"

    def get_queryset(self):
        return Link.objects.filter(user=self.request.user)


# @method_decorator([login_required], name="dispatch")
# class LinkEditRowView(TemplateView):
#     template_name = "modal.html"

#     def get_context_data(self, **kwargs):
#         link = get_object_or_404(Link, pk=kwargs["pk"])
#         form = LinkForm(instance=link)
#         return {"form": form}


class LinkEditRowView(FormView):
    template_name = "modal.html"
    form_class = LinkForm

    def get_success_url(self):
        return reverse_lazy("link-home", kwargs={"pk": self.kwargs["pk"]})

    def get_initial(self):
        link = get_object_or_404(Link, pk=self.kwargs["pk"])
        return {"token": link.token, "target_url": link.target_url}

    def form_valid(self, form):
        link = get_object_or_404(Link, pk=self.kwargs["pk"])
        link.token = form.cleaned_data["token"]
        link.target_url = form.cleaned_data["target_url"]
        link.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        html = render_to_string("form_snippet.html", {"form": form})
        return JsonResponse({"html": html})
        # return render(self.request, "form_snippet.html", {"form": form})
        # return super().form_invalid(form)


@method_decorator([login_required], name="dispatch")
class LinkRowView(TemplateView):
    template_name = "link_row.html"

    def get_context_data(self, **kwargs):
        link = get_object_or_404(Link, pk=kwargs["pk"])
        return {"link": link}


def targetURL(request, token):
    link = get_object_or_404(Link, token=token)
    return redirect(link.target_url)
