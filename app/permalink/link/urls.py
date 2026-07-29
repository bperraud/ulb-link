from django.urls import path

from link.views import views
from mycloud import api as api_views

urlpatterns = [
    path("api/v1/", api_views.ExternalLinkAPIView.as_view()),
    path("api/<int:pk>", api_views.LinkAPIView.as_view(), name="link-api"),
    path("toolbar/<int:nb>", views.toolbar),
    path("edit/<int:pk>", views.edit_link, name="link-edit-row"),
    path("create-link/", views.create_link, name="create-link"),
    path("delete/<str:ids>", views.delete_links),
    path("delete_all/", views.delete_all_links),
    path("row/<int:pk>", views.LinkRowView.as_view(), name="link-row"),
    path("", views.LinkTableView.as_view(), name="link-home"),
]
