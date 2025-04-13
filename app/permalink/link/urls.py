from django.contrib import admin
from django.urls import path

from link.api import LinkCreateAPIView
from link import views

urlpatterns = [
    path("api/", LinkCreateAPIView.as_view(), name="link-create"),
    path("", views.LinkListView.as_view(), name="home"),
]
