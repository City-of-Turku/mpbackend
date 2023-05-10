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
    response = api_client.post(url)
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
    # Test get-result endpoint
    url = reverse("profiles:answer-get-result")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["value"] == "negative result"
    # Test end poll (logout)
    url = reverse("profiles:question-end-poll")
    response = api_client.post(url)
    assert response.status_code == 200
    url = reverse("profiles:answer-list")
    # should return 403 Forbidden
    response = api_client.post(url, {"option": option.id})
    assert response.status_code == 403


@pytest.mark.django_db
def test_questions(api_client, questions, options, results):
    # Test questions list
    url = reverse("profiles:question-list")
    response = api_client.get(url)
    assert len(response.json()["results"]) == questions.count()
    question = questions.first()
    url = reverse("profiles:question-detail", args=[str(question.id)])
    response = api_client.get(url)
    json_response = response.json()
    assert json_response["question"] == question.question
    assert len(json_response["options"]) == options.filter(question=question).count()
    assert (
        json_response["options"][0]["value"]
        == options.filter(question=question).first().value
    )
    assert (
        len(json_response["options"][0]["results"])
        == question.options.first().results.count()
    )
    assert (
        json_response["options"][0]["results"][0]["value"]
        == results.filter(options__question=question).first().value
    )
    # Test get_question by its number
    url = reverse("profiles:question-get-question") + "?number=2"
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["question"] == questions.filter(number=2).first().question
    # Test getting nonexisting question by its number
    url = reverse("profiles:question-get-question") + "?number=2222"
    response = api_client.get(url)
    assert response.status_code == 404
    # Test get_question_number
    url = reverse("profiles:question-get-question-numbers")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["results"][-1]["number"] == questions.last().number
