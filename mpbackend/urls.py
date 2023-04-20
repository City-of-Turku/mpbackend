from django.contrib import admin
from django.urls import include, re_path
from rest_framework import routers

from profiles.api.views import all_views

router = routers.DefaultRouter()
registered_api_views = set()
for view in all_views:
    kwargs = {}
    if view["name"] in registered_api_views:
        continue
    else:
        registered_api_views.add(view["name"])

    if "basename" in view:
        kwargs["basename"] = view["basename"]
    router.register(view["name"], view["class"], **kwargs)


urlpatterns = [
    re_path("^admin/", admin.site.urls),
    re_path(r"^api/v1/", include(router.urls)),
]
