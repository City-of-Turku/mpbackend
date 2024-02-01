from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "account"

# Create a router and register our viewsets with it.
router = routers.DefaultRouter()
router.register("profile", views.ProfileViewSet, "profiles")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("", include(router.urls), name="account")]
