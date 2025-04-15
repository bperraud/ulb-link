from django.urls import path

from link.api import LinkAPIView, createLink
from link.views import LinkListView, LinkEditRowView, LinkRowView

urlpatterns = [
    path("api/", LinkAPIView.as_view(), name="link-post"),
    path("api/create/", createLink, name="link-post"),
    path("api/<int:pk>", LinkAPIView.as_view(), name="link-api"),
    path("edit/<int:pk>", LinkEditRowView.as_view(), name="link-edit-row"),
    path("row/<int:pk>", LinkRowView.as_view(), name="link-row"),
    path("", LinkListView.as_view(), name="link-list"),
    path("<int:pk>", LinkListView.as_view(), name="link-list"),
]
