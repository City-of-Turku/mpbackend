import uuid

import pytest
from django.core import mail
from rest_framework.reverse import reverse

from account.models import User

from .utils import check_method_status_codes, patch

ALL_METHODS = ("get", "post", "put", "patch", "delete")


@pytest.mark.django_db
def test_unauthenticated_cannot_do_anything(api_client, users):
    # TODO, add start-poll url fter recaptcha integration
    urls = [
        reverse("account:profiles-detail", args=[users.first().id]),
    ]
    check_method_status_codes(api_client, urls, ALL_METHODS, 403)


@pytest.mark.django_db
def test_email_verify_process(api_client):
    mail.outbox = []
    test_email = "test@test.com"
    # Test authentication required
    url = reverse("account:profiles-email-verify-request") + "?email=test_mail@test.com"
    response = api_client.get(url)
    assert response.status_code == 403
    url = reverse("profiles:question-start-poll")
    response = api_client.post(url)
    assert response.status_code == 200
    assert User.objects.all().count() == 1
    uid = response.json()["id"]
    user = User.objects.get(pk=uid)
    assert user.email_verified is False
    assert len(mail.outbox) == 0
    url = reverse("account:profiles-email-verify-request") + f"?email={test_email}"
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(mail.outbox) == 1
    verify_msg = None
    for msg in mail.outbox:
        if "Verify" in msg.subject:
            verify_msg = msg
    assert verify_msg
    # Check contains correct uid
    uid = str(user.id)
    assert uid in verify_msg.body
    # Todo fix when send mail msg is ready
    token = verify_msg.body.split()[1]
    url = reverse("account:profiles-email-verify-confirm")
    response = api_client.post(url, {"uid": uid, "token": token})
    assert response.status_code == 200
    user = User.objects.get(pk=uid)
    assert user.email_verified is True
    # Try to use the same token
    response = api_client.post(url, {"uid": uid, "token": token})
    assert response.status_code == 400
    # Nonexisting uid and token values
    response = api_client.post(url, {"uid": uuid.uuid4(), "token": "foobar"})
    assert response.status_code == 400
    # Test save email
    user = User.objects.get(pk=uid)
    assert user.email is None
    url = reverse("account:profiles-save-email")
    response = api_client.post(url, {"email": test_email})
    assert response.status_code == 201
    user = User.objects.get(pk=uid)
    assert user.email == test_email
    # Test duplicate email
    url = reverse("profiles:question-end-poll")
    response = api_client.post(url)
    url = reverse("profiles:question-start-poll")
    response = api_client.post(url)
    url = reverse("account:profiles-save-email")
    response = api_client.post(url, {"email": test_email})
    assert response.status_code == 409


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
def test_profile_patch_age(api_client, users, profiles):
    user = users.first()
    api_client.force_login(user=user)
    url = reverse("account:profiles-detail", args=[user.id])
    patch(api_client, url, {"age": 42})
    user.refresh_from_db()
    assert user.profile.age == 42


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
