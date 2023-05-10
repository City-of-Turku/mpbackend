import uuid

import pytest
from django.core import mail
from rest_framework.reverse import reverse

from account.models import User


@pytest.mark.django_db
def test_email_verify(api_client):
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
    user = User.objects.get(pk=uid)
    assert user.email == test_email
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


@pytest.mark.django_db
def test_profile(api_client):
    url = reverse("profiles:question-start-poll")
    response = api_client.post(url)
    assert response.status_code == 200
    assert User.objects.all().count() == 1
    user = User.objects.first()
    assert user.profile.postal_code is None
    # Test update profile
    url = reverse("account:profiles-detail", args=[user.id])
    response = api_client.put(url, {"postal_code": "20210"})
    assert response.status_code == 201
    user = User.objects.first()
    assert user.profile.postal_code == "20210"
    url = reverse("profiles:question-end-poll")
    response = api_client.post(url)
    # Test update after logout (end-poll)
    url = reverse("account:profiles-detail", args=[user.id])
    response = api_client.put(url, {"postal_code": "20210"})
    assert response.status_code == 403
