import pytest
from rest_framework.reverse import reverse

from account.models import User
from profiles.models import Answer, Option, Question, SubQuestion


@pytest.mark.django_db
def test_poll(
    api_client, questions, sub_questions, question_conditions, options, results
):
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
    answer_url = reverse("profiles:answer-list")
    question1 = Question.objects.get(number="1")
    option = Option.objects.get(question=question1, value="no")
    response = api_client.post(answer_url, {"option": option.id})
    assert Answer.objects.count() == 1
    user = User.objects.first()
    assert user.result.value == "negative result"
    # Answer to sub question
    how_ofter_public_transport_question = Question.objects.get(number="2")
    train_sub_q = SubQuestion.objects.get(
        question=how_ofter_public_transport_question, description="train"
    )
    option = Option.objects.get(sub_question=train_sub_q, value="daily")
    response = api_client.post(answer_url, {"option": option.id})
    assert Answer.objects.count() == 2
    assert Answer.objects.filter(user=user).last().option == option
    # Test get-result endpoint
    url = reverse("profiles:answer-get-result")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["value"] == "negative result"
    # Test test_condition endpoint
    # car not used, so the condition is not met
    condition_url = reverse("profiles:answer-check-if-condition-met")
    response = api_client.post(
        condition_url, {"question_id": Question.objects.get(number="1b").id}
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is False
    question1 = Question.objects.get(number="1")
    option = Option.objects.get(question=question1, value="yes")
    response = api_client.post(answer_url, {"option": option.id})

    # 'yes' answered to car usage and the condition is met
    response = api_client.post(
        condition_url, {"question_id": Question.objects.get(number="1b").id}
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is True

    # sub_queston train is answered with 'daily' so the condition is met
    response = api_client.post(
        condition_url, {"question_id": Question.objects.get(number="3").id}
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is True

    # Test end poll (logout)
    url = reverse("profiles:question-end-poll")
    response = api_client.post(url)
    assert response.status_code == 200
    url = reverse("profiles:answer-list")
    # should return 403 Forbidden as end_poll has logged out the user
    response = api_client.post(url, {"option": option.id})
    assert response.status_code == 403


@pytest.mark.django_db
def test_questions(api_client, questions, question_conditions, options, results):
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
