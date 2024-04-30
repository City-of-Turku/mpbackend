import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from account.api.views import ProfileViewSet
from account.models import MailingList, MailingListEmail, Profile, User
from profiles.models import Result


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_client_authenticated(users):
    user = users.get(username="test1")
    token = Token.objects.create(user=user)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return api_client


@pytest.fixture()
def api_client_with_custom_ip_address(ip_address):
    return APIClient(REMOTE_ADDR=ip_address)


@pytest.fixture
def users(results):
    [
        User.objects.create(username=f"test{i}", result=results[i % results.count()])
        for i in range(4)
    ]
    return User.objects.all()


@pytest.fixture
def throttling_users(results):
    num_users = (
        int(ProfileViewSet.unsubscribe.kwargs["throttle_classes"][0].rate.split("/")[0])
        + 2
    )
    [
        User.objects.create(username=f"t_test{i}", result=results[i % results.count()])
        for i in range(num_users)
    ]
    return User.objects.all()


@pytest.fixture
def profiles(users):
    test_user = User.objects.get(username="test1")
    Profile.objects.create(user=test_user)
    return Profile.objects.all()


@pytest.fixture
def results():
    Result.objects.create(topic="Car traveller")
    Result.objects.create(topic="Habit traveller")
    return Result.objects.all()


@pytest.fixture
def mailing_lists(results):
    MailingList.objects.create(result=results.first())
    return MailingList.objects.all()


@pytest.fixture
def mailing_list_emails(mailing_lists):
    [
        MailingListEmail.objects.create(
            email=f"test_{c}@test.com", mailing_list=mailing_lists.first()
        )
        for c in range(52)
    ]
    return MailingListEmail.objects.all()
