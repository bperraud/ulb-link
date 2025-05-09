from django.urls import path

from link.api import ExternalLinkAPIView, LinkAPIView
from link.views import LinkListView, LinkRowView, edit_link

urlpatterns = [
    path("api/create/", ExternalLinkAPIView.as_view(), name="external-api"),
    path("api/<int:pk>", LinkAPIView.as_view(), name="link-api"),
    path("edit/<int:pk>", edit_link, name="link-edit-row"),
    path("row/<int:pk>", LinkRowView.as_view(), name="link-row"),
    path("", LinkListView.as_view(), name="link-home"),
    path("<int:pk>", LinkListView.as_view(), name="link-home"),
]
