from django.urls import path

from mycloud.api import ExternalLinkAPIView, LinkAPIView
from mycloud import views

urlpatterns = [
    # path("api/v0/", ExternalLinkAPIView.as_view()),
    # path("api/<int:pk>", LinkAPIView.as_view(), name="link-api"),
    path("create-bulk/", views.create_bulk, name="create-bulk"),
    path(
        "create-nextcloud-bulk/",
        views.create_nextcloud_bulk,
        name="create-nextcloud-bulk",
    ),
    path(
        "row/<int:pk>",
        views.MycloudLinkRowView.as_view(),
        name="mycloud-link-row",
    ),
    path(
        "renew_expiration",
        views.renew_expiration,
        name="mycloud-renew-expiration",
    ),
    path("", views.MycloudLinkTableView.as_view(), name="mycloud-link"),
    path(
        "bulk_advancement",
        views.bulk_task_advancement,
        name="bulk-task-advancement",
    ),
]
