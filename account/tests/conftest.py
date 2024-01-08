import pytest
from rest_framework.test import APIClient

from account.models import Profile, User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def users():
    User.objects.create(username="test1")
    return User.objects.all()


@pytest.fixture
def profiles(users):
    test_user = User.objects.get(username="test1")
    Profile.objects.create(user=test_user)
    return Profile.objects.all()
