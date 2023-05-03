import pytest
from rest_framework.reverse import reverse

from account.models import User
from profiles.models import Answer, Option


@pytest.mark.django_db
def test_poll(api_client, questions, options, results):
    url = reverse("profiles:question-list")
    response = api_client.get(url)
    assert response.status_code == 200
    # Test create answer, when poll is not started
    url = reverse("profiles:answer-list")
    response = api_client.post(url)
    assert response.status_code == 403
    # Test poll start
    User.objects.all().count() == 0
    url = reverse("profiles:question-start-poll")
    response = api_client.get(url)
    assert response.status_code == 200
    User.objects.all().count() == 1
    # Test answer
    assert Answer.objects.count() == 0
    url = reverse("profiles:answer-list")
    option = Option.objects.get(value="no")
    response = api_client.post(url, {"option": option.id})
    assert Answer.objects.count() == 1
    user = User.objects.first()
    assert user.result.value == "negative result"
