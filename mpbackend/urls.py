from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# import account.api.urls
import profiles.api.urls

# router = routers.DefaultRouter()
# registered_api_views = set()

# for view in profiles_views + account_views:
#     kwargs = {}
#     if view["name"] in registered_api_views:
#         continue
#     else:
#         registered_api_views.add(view["name"])

#     if "basename" in view:
#         kwargs["basename"] = view["basename"]
#     router.register(view["name"], view["class"], **kwargs)


# from profiles.api.urls import router as profiles_router
# from account.api.urls import router as account_router
# router = routers.DefaultRouter()
# router.registry.extend(profiles_router.registry)
# router.registry.extend(account_router.registry)

urlpatterns = [
    re_path("^admin/", admin.site.urls),
    # re_path(r"^api/v1/", include(router.urls)),
    # re_path(r"^api/account/", include(account.api.urls), name="account"),
    re_path(r"^api/v1/", include(profiles.api.urls), name="profiles"),
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
    # path("api-auth/", include("rest_framework.urls")),
]
