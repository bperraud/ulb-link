"""
URL configuration for permalink project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf.urls.static import static

from link.views.views import targetURL, status
from link.views.account_views import login_view, auth_callback
from django.contrib.auth import views as auth_views
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("status/", status),
    path("link/", include("link.urls")),
    path("t/<str:token>", targetURL, name="redirect"),
    path("", RedirectView.as_view(url="/link/", permanent=False)),
    # auth
    path("accounts/login/", login_view, name="login"),
    path("auth/callback/", auth_callback, name="auth_callback"),
    # path(
    #     "accounts/login/",
    #     auth_views.LoginView.as_view(template_name="login.html", next_page="link-home"),
    #     name="login",
    # ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page="login"),
        name="logout",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
