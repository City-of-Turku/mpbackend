import time
from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.reverse import reverse

from account.api.views import ProfileViewSet
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
        ("1.1.1.1"),
    ],
)
def test_mailing_list_unsubscribe_throttling(
    api_client_with_custom_ip_address, mailing_list_emails
):
    # Set number of requests to be made from the rate. The rate is stored as a string, e.g., rate = "10/day"
    num_requests = int(
        ProfileViewSet.unsubscribe.kwargs["throttle_classes"][0].rate.split("/")[0]
    )
    url = reverse("account:profiles-unsubscribe")
    count = 0
    while count < num_requests:
        response = api_client_with_custom_ip_address.post(
            url, {"email": f"test_{count}@test.com"}
        )
        assert response.status_code == 200, response.content
        count += 1
    time.sleep(2)
    response = api_client_with_custom_ip_address.post(
        url, {"email": f"test_{count}@test.com"}
    )
    assert response.status_code == 429


@pytest.mark.django_db
def test_profile_created(api_client):
    url = reverse("profiles:question-start-poll")
    response = api_client.post(url)
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
    assert user.profile.gender is None
    assert user.profile.postal_code is None
    assert user.profile.optional_postal_code is None
    assert user.profile.result_can_be_used is True
    data = {
        "postal_code": "20210",
        "optional_postal_code": "20220",
        "is_interested_in_mobility": True,
        "gender": "F",
        "result_can_be_used": False,
    }
    response = api_client_authenticated.put(url, data)
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.profile.is_interested_in_mobility is True
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
def test_profile_patch_result_can_be_used(api_client_authenticated, users, profiles):
    user = users.get(username="test1")
    url = reverse("account:profiles-detail", args=[user.id])
    assert user.profile.result_can_be_used is True
    patch(api_client_authenticated, url, {"result_can_be_used": False})
    user.refresh_from_db()
    assert user.profile.result_can_be_used is False


@pytest.mark.django_db
def test_mailing_list_subscribe(api_client, users, results):
    url = reverse("account:profiles-subscribe")
    user = users.get(username="test1")
    response = api_client.post(url, {"email": "test@test.com", "user": user.id})
    assert response.status_code == 201
    assert MailingListEmail.objects.count() == 1
    assert MailingListEmail.objects.first().email == "test@test.com"
    assert (
        MailingList.objects.filter(result=user.result).first().emails.first()
        == MailingListEmail.objects.first()
    )
    assert MailingList.objects.first().result == user.result


@pytest.mark.django_db
def test_mailing_user_has_subscribed(api_client, users, results, mailing_lists):
    url = reverse("account:profiles-subscribe")
    response = api_client.post(
        url, {"email": "test@test.com", "user": users.first().id}
    )
    assert response.status_code == 201
    response = api_client.post(
        url, {"email": "test@test.com", "user": users.first().id}
    )
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ip_address",
    [
        ("1.1.1.2"),
    ],
)
def test_mailing_list_subscribe_throttling(
    api_client_with_custom_ip_address, throttling_users
):
    num_requests = int(
        ProfileViewSet.subscribe.kwargs["throttle_classes"][0].rate.split("/")[0]
    )
    url = reverse("account:profiles-subscribe")
    count = 0
    while count < num_requests:
        response = api_client_with_custom_ip_address.post(
            url,
            {
                "email": f"throttlling_test_{count}@test.com",
                "user": throttling_users[count].id,
            },
        )
        assert response.status_code == 201, response.content
        count += 1

    time.sleep(2)
    response = api_client_with_custom_ip_address.post(
        url, {"email": f"test_{count}@test.com", "user": throttling_users[count].id}
    )
    assert response.status_code == 429


@pytest.mark.django_db
def test_mailing_list_is_created_on_subscribe(api_client, users, results):
    assert MailingList.objects.count() == 0
    url = reverse("account:profiles-subscribe")
    response = api_client.post(
        url, {"email": "test@test.com", "user": users.first().id}
    )
    assert response.status_code == 201
    assert MailingList.objects.count() == 1
    assert MailingListEmail.objects.count() == 1


@pytest.mark.django_db
def test_mailing_list_subscribe_with_invalid_emails(api_client, users, results):
    assert MailingList.objects.count() == 0
    url = reverse("account:profiles-subscribe")
    for email in [
        "john.doe@company&.com",
        "invalid-email.com",
        "john.doe@",
        "john.doe@example",
        "john.doe@example",
    ]:
        response = api_client.post(url, {"email": email, "user": users.first().id})
        assert response.status_code == 400
        assert MailingList.objects.count() == 0
        assert MailingList.objects.count() == 0


@pytest.mark.django_db
def test_mailing_list_subscribe_with_invalid_post_data(
    api_client_authenticated, users, results
):
    url = reverse("account:profiles-subscribe")
    # Missing email
    response = api_client_authenticated.post(url, {"user": users.first().id})
    assert response.status_code == 400
    assert MailingList.objects.count() == 0
    # Missing result
    response = api_client_authenticated.post(url, {"email": "test@test.com"})
    assert response.status_code == 400
    assert MailingList.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ip_address",
    [
        ("1.1.1.3"),
    ],
)
def test_mailing_list_unsubscribe(
    api_client_with_custom_ip_address, mailing_list_emails
):
    num_mailing_list_emails = mailing_list_emails.count()
    assert MailingListEmail.objects.count() == num_mailing_list_emails
    assert MailingList.objects.first().emails.count() == num_mailing_list_emails
    url = reverse("account:profiles-unsubscribe")
    response = api_client_with_custom_ip_address.post(url, {"email": "test_0@test.com"})
    assert response.status_code == 200
    assert MailingListEmail.objects.count() == num_mailing_list_emails - 1
    assert MailingList.objects.first().emails.count() == num_mailing_list_emails - 1


@pytest.mark.django_db
@pytest.mark.django_db
@pytest.mark.parametrize(
    "ip_address",
    [
        ("1.1.1.4"),
    ],
)
def test_mailing_list_unsubscribe_non_existing_email(
    api_client_with_custom_ip_address, mailing_list_emails
):
    num_mailing_list_emails = mailing_list_emails.count()
    assert MailingListEmail.objects.count() == num_mailing_list_emails
    assert MailingList.objects.first().emails.count() == num_mailing_list_emails
    url = reverse("account:profiles-unsubscribe")
    response = api_client_with_custom_ip_address.post(
        url, {"email": "idonotexist@test.com"}
    )
    assert response.status_code == 400
    assert MailingListEmail.objects.count() == num_mailing_list_emails
    assert MailingList.objects.first().emails.count() == num_mailing_list_emails


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ip_address",
    [
        ("1.1.1.5"),
    ],
)
def test_mailing_list_unsubscribe_email_not_provided(
    api_client_with_custom_ip_address, mailing_list_emails
):
    url = reverse("account:profiles-unsubscribe")
    response = api_client_with_custom_ip_address.post(url)
    assert response.status_code == 400
