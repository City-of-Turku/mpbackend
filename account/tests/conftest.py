import pytest
from rest_framework.test import APIClient

from account.models import MailingList, MailingListEmail, Profile, User
from profiles.models import Result


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
    MailingListEmail.objects.create(
        email="test@test.com", mailing_list=mailing_lists.first()
    )
    MailingListEmail.objects.create(
        email="abc@efg.com", mailing_list=mailing_lists.first()
    )
    return MailingListEmail.objects.all()
