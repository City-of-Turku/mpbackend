import time
from datetime import timedelta
from unittest.mock import patch as mock_patch

import pytest
from django.conf import settings
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.reverse import reverse

from account.models import MailingList, MailingListEmail, User
from profiles.models import PostalCode, PostalCodeResult

from .utils import check_method_status_codes, patch

ALL_METHODS = ("get", "post", "put", "patch", "delete")


@pytest.mark.django_db
def test_token_expiration(api_client_authenticated, users, profiles):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    with freeze_time(
        timezone.now() + timedelta(hours=settings.TOKEN_EXPIRED_AFTER_HOURS - 1)
    ):
        patch(api_client_authenticated, url, {"year_of_birth": 42})

    with freeze_time(
        timezone.now() + timedelta(hours=settings.TOKEN_EXPIRED_AFTER_HOURS + 1)
    ):
        patch(api_client_authenticated, url, {"year_of_birth": 42}, 401)


@pytest.mark.django_db
def test_unauthenticated_cannot_do_anything(api_client, users):
    urls = [
        reverse("account:profiles-detail", args=[users.get(username="test1").id]),
    ]
    check_method_status_codes(api_client, urls, ALL_METHODS, 401)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ip_address",
    [
        ("192.168.1.40"),
    ],
)
def test_mailing_list_unsubscribe_throttling(
    api_client_with_custom_ip_address, mailing_list_emails
):
    num_requests = 10
    url = reverse("account:profiles-unsubscribe")
    count = 0
    while count < num_requests:
        response = api_client_with_custom_ip_address.post(
            url, {"email": f"test_{count}@test.com"}
        )
        assert response.status_code == 200
        count += 1
    time.sleep(2)
    response = api_client_with_custom_ip_address.post(
        url, {"email": f"test_{count}@test.com"}
    )
    assert response.status_code == 429


@pytest.mark.django_db
@mock_patch("profiles.api.views.verify_recaptcha")
def test_profile_created(verify_recaptcha_mock, api_client):
    verify_recaptcha_mock.return_value = True
    url = reverse("profiles:question-start-poll")
    response = api_client.post(url, {"token": "foo"})
    assert response.status_code == 200
    assert User.objects.all().count() == 1
    user = User.objects.first()
    assert user.is_generated is True
    assert user.profile.postal_code is None


@pytest.mark.django_db
def test_profile_put_creates_postal_code_result(
    api_client_authenticated, users, profiles
):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    data = {
        "postal_code": "20210",
        "optional_postal_code": "20220",
    }
    response = api_client_authenticated.put(url, data)
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 2
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code="20210")
        ).count
        == 1
    )
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code="20220")
        ).count
        == 1
    )


@pytest.mark.django_db
def test_profile_put_not_creates_postal_code_result(
    api_client_authenticated, users, profiles
):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    data = {"year_of_birth": 42}
    response = api_client_authenticated.put(url, data)
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 0


@pytest.mark.django_db
def test_profile_put(api_client_authenticated, users, profiles):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    assert user.profile.is_interested_in_mobility is False
    assert user.profile.is_filled_for_fun is False
    assert user.profile.gender is None
    assert user.profile.postal_code is None
    assert user.profile.optional_postal_code is None
    assert user.profile.result_can_be_used is True
    data = {
        "postal_code": "20210",
        "optional_postal_code": "20220",
        "is_interested_in_mobility": True,
        "gender": "F",
        "is_filled_for_fun": True,
        "result_can_be_used": False,
    }
    response = api_client_authenticated.put(url, data)
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.profile.is_interested_in_mobility is True
    assert user.profile.is_filled_for_fun is True
    assert user.profile.gender == "F"
    assert user.profile.postal_code == "20210"
    assert user.profile.optional_postal_code == "20220"
    assert user.profile.result_can_be_used is False


@pytest.mark.django_db
def test_profile_patch_is_interested_in_mobility(
    api_client_authenticated, users, profiles
):
    user = users.get(username="test1")
    assert user.profile.is_interested_in_mobility is False
    url = reverse("account:profiles-detail", args=[user.id])
    patch(api_client_authenticated, url, {"is_interested_in_mobility": True})
    user.refresh_from_db()
    assert user.profile.is_interested_in_mobility is True


@pytest.mark.django_db
def test_profile_patch_geneder(api_client_authenticated, users, profiles):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    patch(api_client_authenticated, url, {"gender": "X"})
    user.refresh_from_db()
    assert user.profile.gender == "X"
    assert PostalCodeResult.objects.count() == 0


@pytest.mark.django_db
def test_profile_patch_postal_code(api_client_authenticated, users, profiles):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    patch(api_client_authenticated, url, {"postal_code": "20210"})
    user.refresh_from_db()
    assert user.profile.postal_code == "20210"
    assert PostalCodeResult.objects.count() == 0


@pytest.mark.django_db
def test_profile_patch_postal_code_unauthenticated(api_client, users, profiles):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    # Test update after logout (end-poll)
    patch(api_client, url, {"postal_code": "20210"}, status_code=401)


@pytest.mark.django_db
def test_profile_patch_optional_postal_code(api_client_authenticated, users, profiles):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    patch(api_client_authenticated, url, {"optional_postal_code": "20100"})
    user.refresh_from_db()
    assert user.profile.optional_postal_code == "20100"
    url = reverse("profiles:question-end-poll")


@pytest.mark.django_db
def test_profile_patch_year_of_birth(api_client_authenticated, users, profiles):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    patch(api_client_authenticated, url, {"year_of_birth": 42})
    user.refresh_from_db()
    assert user.profile.year_of_birth == 42


@pytest.mark.django_db
def test_profile_patch_is_filled_for_fun(api_client_authenticated, users, profiles):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    assert user.profile.is_filled_for_fun is False
    patch(api_client_authenticated, url, {"is_filled_for_fun": True})
    user.refresh_from_db()
    assert user.profile.is_filled_for_fun is True


@pytest.mark.django_db
def test_profile_patch_result_can_be_used(api_client_authenticated, users, profiles):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    assert user.profile.result_can_be_used is True
    patch(api_client_authenticated, url, {"result_can_be_used": False})
    user.refresh_from_db()
    assert user.profile.result_can_be_used is False


@pytest.mark.django_db
def test_mailing_list_unauthenticated_subscribe(api_client, results):
    url = reverse("account:profiles-subscribe")
    response = api_client.post(
        url, {"email": "test@test.com", "result": results.first().id}
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_mailing_list_subscribe(
    api_client_authenticated, users, results, mailing_lists
):
    url = reverse("account:profiles-subscribe")
    response = api_client_authenticated.post(
        url, {"email": "test@test.com", "result": results.first().id}
    )
    assert response.status_code == 201
    assert MailingListEmail.objects.count() == 1
    assert MailingListEmail.objects.first().email == "test@test.com"
    assert (
        MailingList.objects.first().emails.first() == MailingListEmail.objects.first()
    )


@pytest.mark.django_db
def test_mailing_list_is_created_on_subscribe(api_client_authenticated, users, results):
    assert MailingList.objects.count() == 0
    url = reverse("account:profiles-subscribe")
    response = api_client_authenticated.post(
        url, {"email": "test@test.com", "result": results.first().id}
    )
    assert response.status_code == 201
    assert MailingList.objects.count() == 1
    assert MailingListEmail.objects.count() == 1


@pytest.mark.django_db
def test_mailing_list_subscribe_with_invalid_emails(
    api_client_authenticated, users, results
):
    assert MailingList.objects.count() == 0
    url = reverse("account:profiles-subscribe")
    for email in [
        "john.doe@company&.com",
        "invalid-email.com",
        "john.doe@",
        "john.doe@example",
        "john.doe@example",
    ]:
        response = api_client_authenticated.post(
            url, {"email": email, "result": results.first().id}
        )
        assert response.status_code == 400
        assert MailingList.objects.count() == 0
        assert MailingList.objects.count() == 0


@pytest.mark.django_db
def test_mailing_list_subscribe_with_invalid_post_data(
    api_client_authenticated, users, results
):
    url = reverse("account:profiles-subscribe")
    # Missing email
    response = api_client_authenticated.post(url, {"result": results.first().id})
    assert response.status_code == 400
    assert MailingList.objects.count() == 0
    assert MailingList.objects.count() == 0
    # Missing result
    response = api_client_authenticated.post(url, {"email": "test@test.com"})
    assert response.status_code == 400
    assert MailingList.objects.count() == 0
    assert MailingList.objects.count() == 0


@pytest.mark.django_db
def test_mailing_list_unsubscribe(api_client, mailing_list_emails):
    num_mailing_list_emails = mailing_list_emails.count()
    assert MailingListEmail.objects.count() == num_mailing_list_emails
    assert MailingList.objects.first().emails.count() == num_mailing_list_emails
    url = reverse("account:profiles-unsubscribe")
    response = api_client.post(url, {"email": "test_0@test.com"})
    assert response.status_code == 200
    assert MailingListEmail.objects.count() == num_mailing_list_emails - 1
    assert MailingList.objects.first().emails.count() == num_mailing_list_emails - 1


@pytest.mark.django_db
def test_mailing_list_unsubscribe_non_existing_email(api_client, mailing_list_emails):
    num_mailing_list_emails = mailing_list_emails.count()
    assert MailingListEmail.objects.count() == num_mailing_list_emails
    assert MailingList.objects.first().emails.count() == num_mailing_list_emails
    url = reverse("account:profiles-unsubscribe")
    response = api_client.post(url, {"email": "idonotexist@test.com"})
    assert response.status_code == 400
    assert MailingListEmail.objects.count() == num_mailing_list_emails
    assert MailingList.objects.first().emails.count() == num_mailing_list_emails


@pytest.mark.django_db
def test_mailing_list_unsubscribe_email_not_provided(api_client, mailing_list_emails):
    url = reverse("account:profiles-unsubscribe")
    response = api_client.post(url)
    assert response.status_code == 400
