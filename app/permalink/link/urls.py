from django.urls import path

from link.api import ExternalLinkAPIView, LinkAPIView
from link.views import views
from link.views import nextcloud_views
from link.views import nextcloud_utils

urlpatterns = [
    path("api/v1/", ExternalLinkAPIView.as_view()),
    path("api/<int:pk>", LinkAPIView.as_view(), name="link-api"),
    path("toolbar/<int:nb>", views.toolbar),
    path("edit/<int:pk>", views.edit_link, name="link-edit-row"),
    path("create-link/", views.create_link, name="create-link"),
    path("create-bulk/", nextcloud_views.create_bulk, name="create-bulk"),
    path(
        "create-nextcloud-bulk/",
        nextcloud_views.create_nextcloud_bulk,
        name="create-nextcloud-bulk",
    ),
    path("delete/<str:ids>", views.delete_links),
    path("row/<int:pk>", views.LinkRowView.as_view(), name="link-row"),
    path(
        "mycloud/row/<int:pk>",
        nextcloud_views.MycloudLinkRowView.as_view(),
        name="mycloud-link-row",
    ),
    path("", views.LinkTableView.as_view(), name="link-home"),
    path(
        "mycloud", nextcloud_views.MycloudLinkTableView.as_view(), name="mycloud-link"
    ),
    path("update/share/<int:id>", nextcloud_utils.update_share_in_nextcloud),
]
