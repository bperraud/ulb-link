from django.contrib import admin
from django.urls import path

from link.api import LinkCreateAPIView
from link.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("/", home),
    path("api/", LinkCreateAPIView.as_view(), name="link-create"),
]
