from django.contrib import admin
from django.urls import include, path, re_path

import profiles.api.urls

urlpatterns = [
    re_path("^admin/", admin.site.urls),
    re_path(r"^api/v1/", include(profiles.api.urls), name="profiles"),
    # TODO, remove
    path("api-auth/", include("rest_framework.urls")),
]
