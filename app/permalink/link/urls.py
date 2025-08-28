from django.urls import path

from link.views.nextcloud_views import update_share_in_nextcloud
from link.api import ExternalLinkAPIView, LinkAPIView
from link.views.views import *

urlpatterns = [
    path("api/external/", ExternalLinkAPIView.as_view(), name="external-api"),
    path("api/<int:pk>", LinkAPIView.as_view(), name="link-api"),
    path("toolbar/<int:nb>", toolbar),
    path("edit/<int:pk>", edit_link, name="link-edit-row"),
    path("create-link/", create_link, name="create-link"),
    path("delete/<str:ids>", delete_links),
    path("row/<int:pk>", LinkRowView.as_view(), name="link-row"),
    path("mycloud/row/<int:pk>", MycloudLinkRowView.as_view(), name="mycloud-link-row"),
    path("", LinkTableView.as_view(), name="link-home"),
    path("mycloud", MycloudLinkTableView.as_view(), name="mycloud-link"),
    path("update/share/<int:id>", update_share_in_nextcloud),
]
