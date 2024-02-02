# from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

import account.api.urls
import profiles.api.urls

urlpatterns = [
    re_path("^admin/", admin.site.urls),
    re_path(r"^api/account/", include(account.api.urls), name="account"),
    re_path(r"^api/v1/", include(profiles.api.urls), name="profiles"),
    # path("api-auth/", include("rest_framework.urls")),
]

# NOTE, consider disabling in production. if settings.DEBUG:
urlpatterns += [
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/v1/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
