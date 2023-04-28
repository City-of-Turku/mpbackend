from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "user_profiles_api"

# Create a router and register our viewsets with it.
router = routers.SimpleRouter()
router.register("user_profiles", views.ProfileViewSet, app_name)

# The API URLs are now determined automatically by the router.
urlpatterns = [path("", include(router.urls))]
