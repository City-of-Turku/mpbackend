import time

import pytest
from rest_framework.reverse import reverse

from account.models import MailingList, MailingListEmail, User

from .utils import check_method_status_codes, patch

ALL_METHODS = ("get", "post", "put", "patch", "delete")


@pytest.mark.django_db
def test_unauthenticated_cannot_do_anything(api_client, users):
    # TODO, add start-poll url after recaptcha integration
    urls = [
        reverse("account:profiles-detail", args=[users.first().id]),
    ]
    check_method_status_codes(api_client, urls, ALL_METHODS, 403)


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
def test_profile_created(api_client):
    url = reverse("profiles:question-start-poll")
    response = api_client.post(url)
    assert response.status_code == 200
    assert User.objects.all().count() == 1
    user = User.objects.first()
    assert user.is_generated is True
    assert user.profile.postal_code is None


@pytest.mark.django_db
def test_profile_patch_postal_code(api_client, users, profiles):
    user = users.first()
    api_client.force_login(user=user)
    url = reverse("account:profiles-detail", args=[user.id])
    patch(api_client, url, {"postal_code": "20210"})
    user.refresh_from_db()
    assert user.profile.postal_code == "20210"
    api_client.post(reverse("profiles:question-end-poll"))
    # Test update after logout (end-poll)
    patch(api_client, url, {"postal_code": "20210"}, status_code=403)


@pytest.mark.django_db
def test_profile_patch_optional_postal_code(api_client, users, profiles):
    user = users.first()
    api_client.force_login(user=user)
    url = reverse("account:profiles-detail", args=[user.id])
    patch(api_client, url, {"optional_postal_code": "20100"})
    user.refresh_from_db()
    assert user.profile.optional_postal_code == "20100"
    url = reverse("profiles:question-end-poll")


@pytest.mark.django_db
def test_profile_patch_year_of_birth(api_client, users, profiles):
    user = users.first()
    api_client.force_login(user=user)
    url = reverse("account:profiles-detail", args=[user.id])
    patch(api_client, url, {"year_of_birth": 42})
    user.refresh_from_db()
    assert user.profile.year_of_birth == 42


@pytest.mark.django_db
def test_profile_patch_is_filled_for_fun(api_client, users, profiles):
    user = users.first()
    api_client.force_login(user=user)
    url = reverse("account:profiles-detail", args=[user.id])
    assert user.profile.is_filled_for_fun is False
    patch(api_client, url, {"is_filled_for_fun": True})
    user.refresh_from_db()
    assert user.profile.is_filled_for_fun is True


@pytest.mark.django_db
def test_profile_patch_result_can_be_used(api_client, users, profiles):
    user = users.first()
    api_client.force_login(user=user)
    url = reverse("account:profiles-detail", args=[user.id])
    assert user.profile.result_can_be_used is True
    patch(api_client, url, {"result_can_be_used": False})
    user.refresh_from_db()
    assert user.profile.result_can_be_used is False


@pytest.mark.django_db
def test_mailing_list_unauthenticated_subscribe(api_client, results):
    url = reverse("account:profiles-subscribe")
    response = api_client.post(
        url, {"email": "test@test.com", "result": results.first().id}
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_mailing_list_subscribe(api_client, users, results, mailing_lists):
    user = users.first()
    api_client.force_login(user=user)
    url = reverse("account:profiles-subscribe")
    response = api_client.post(
        url, {"email": "test@test.com", "result": results.first().id}
    )
    assert response.status_code == 201
    assert MailingListEmail.objects.count() == 1
    assert MailingListEmail.objects.first().email == "test@test.com"
    assert (
        MailingList.objects.first().emails.first() == MailingListEmail.objects.first()
    )


@pytest.mark.django_db
def test_mailing_list_is_created_on_subscribe(api_client, users, results):
    assert MailingList.objects.count() == 0
    api_client.force_login(user=users.first())
    url = reverse("account:profiles-subscribe")
    response = api_client.post(
        url, {"email": "test@test.com", "result": results.first().id}
    )
    assert response.status_code == 201
    assert MailingList.objects.count() == 1
    assert MailingListEmail.objects.count() == 1


@pytest.mark.django_db
def test_mailing_list_subscribe_with_invalid_emails(api_client, users, results):
    assert MailingList.objects.count() == 0
    api_client.force_login(user=users.first())
    url = reverse("account:profiles-subscribe")
    for email in [
        "john.doe@company&.com",
        "invalid-email.com",
        "john.doe@",
        "john.doe@example",
        "john.doe@example",
    ]:
        response = api_client.post(url, {"email": email, "result": results.first().id})
        assert response.status_code == 400
        assert MailingList.objects.count() == 0
        assert MailingList.objects.count() == 0


@pytest.mark.django_db
def test_mailing_list_subscribe_with_invalid_post_data(api_client, users, results):
    api_client.force_login(user=users.first())
    url = reverse("account:profiles-subscribe")
    # Missing email
    response = api_client.post(url, {"result": results.first().id})
    assert response.status_code == 400
    assert MailingList.objects.count() == 0
    assert MailingList.objects.count() == 0
    # Missing result
    response = api_client.post(url, {"email": "test@test.com"})
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
