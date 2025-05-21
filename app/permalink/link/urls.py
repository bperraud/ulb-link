from django.urls import path

from link.views.nextcloud_views import update_share_in_nextcloud, update_shares_object
from link.api import ExternalLinkAPIView, LinkAPIView
from link.views.views import LinkListView, LinkRowView, edit_link, delete_links, toolbar

urlpatterns = [
    path("api/external/", ExternalLinkAPIView.as_view(), name="external-api"),
    path("api/<int:pk>", LinkAPIView.as_view(), name="link-api"),
    path("toolbar/<int:nb>", toolbar),
    path("edit/<int:pk>", edit_link, name="link-edit-row"),
    path("delete/<str:ids>", delete_links),
    path("row/<int:pk>", LinkRowView.as_view(), name="link-row"),
    path("", LinkListView.as_view(), name="link-home"),
    path("<int:pk>", LinkListView.as_view(), name="link-home"),
    path("update/share/<int:id>", update_share_in_nextcloud),
]
