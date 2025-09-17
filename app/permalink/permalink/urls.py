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

from mozilla_django_oidc.views import OIDCAuthenticationRequestView
from link.views.views import redirect_to_target_url, status
from link.auth import OIDCCallbackView
from link.views.account_views import auth_callback, mycloud_login_view, logout_view
# from django.contrib.auth import views as auth_views
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("status/", status),
    path("link/", include("link.urls")),
    path("t/<str:token>", redirect_to_target_url, name="redirect"),
    path("", RedirectView.as_view(url="/link/", permanent=False), name='home'),
    # auth
    # path("accounts/login/", login_view, name="login"),
    path("accounts/login/", OIDCAuthenticationRequestView.as_view(), name="login"),
    # path("accounts/login/", login_view, name="login"),
    path("oidc/callback/", OIDCCallbackView.as_view(), name="oidc_authentication_callback"),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path("accounts/login/mycloud/", mycloud_login_view, name="mycloud_login"),
    path("auth/callback/", auth_callback, name="auth_callback"),
    path(
        "accounts/logout/",
        logout_view,
        # auth_views.LogoutView.as_view(next_page="login"),
        name="logout",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
