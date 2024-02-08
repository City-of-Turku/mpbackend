import pytest
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse

from account.models import User
from profiles.models import Answer, Option, Question, SubQuestion


def test_answer_post_unauthenticated(api_client):
    url = reverse("profiles:answer-list")
    response = api_client.post(url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_poll_start(api_client):
    User.objects.all().count() == 0
    url = reverse("profiles:question-start-poll")
    response = api_client.post(url)
    assert response.status_code == 200
    User.objects.all().count() == 1


@pytest.mark.django_db
def test_post_answer(api_client_authenticated, users, questions, options):
    user = users.get(username="test1")
    assert Answer.objects.count() == 0
    answer_url = reverse("profiles:answer-list")
    question1 = questions.get(number="1")
    option = options.get(question=question1, value="no")
    response = api_client_authenticated.post(
        answer_url, {"option": option.id, "question": question1.id}
    )
    assert response.status_code == 201
    assert Answer.objects.count() == 1
    user.refresh_from_db()
    assert user.result.value == "negative result"


@pytest.mark.django_db
def test_post_answer_with_other_option(api_client, users, answers, questions, options):
    user = users.get(username="no answers user")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    option = options.get(value="other")
    question3 = questions.get(number="3")
    answer_url = reverse("profiles:answer-list")
    response = api_client.post(
        answer_url,
        {"option": option.id, "question": question3.id, "other": "test data"},
    )
    assert response.status_code == 201
    answers_qs = Answer.objects.filter(user=user)
    assert answers_qs.count() == 1
    assert answers_qs.first().other == "test data"
    # Test posting without 'other' field to a option where is_other is True
    response = api_client.post(
        answer_url, {"option": option.id, "question": question3.id}
    )
    assert response.status_code == 400
    answers_qs = Answer.objects.filter(user=user)
    assert answers_qs.count() == 1


@pytest.mark.django_db
def test_post_answer_answer_is_updated(
    api_client_authenticated, users, answers, questions, options
):
    user = users.get(username="test1")
    answer = answers.filter(user=user).first()
    question = answer.question
    option = answer.option
    assert option.value == "no"
    new_option = options.get(value="yes")
    answer_url = reverse("profiles:answer-list")
    api_client_authenticated.post(
        answer_url, {"option": new_option.id, "question": question.id}
    )
    answer.refresh_from_db()
    assert answer.option.value == "yes"


@pytest.mark.django_db
def test_post_answer_to_sub_question(
    api_client_authenticated, users, questions, sub_questions, options
):
    user = users.get(username="test1")
    answer_url = reverse("profiles:answer-list")
    how_ofter_public_transport_question = Question.objects.get(number="2")
    train_sub_q = SubQuestion.objects.get(
        question=how_ofter_public_transport_question, description="train"
    )
    option = Option.objects.get(sub_question=train_sub_q, value="daily")
    response = api_client_authenticated.post(
        answer_url,
        {
            "option": option.id,
            "question": how_ofter_public_transport_question.id,
            "sub_question": train_sub_q.id,
        },
    )
    assert response.status_code == 201
    assert Answer.objects.count() == 1
    assert Answer.objects.filter(user=user).first().option == option


@pytest.mark.django_db
def test_post_answer_where_question_not_related_to_option(
    api_client_authenticated, users, questions, sub_questions, options
):
    answer_url = reverse("profiles:answer-list")
    train_sub_q = sub_questions.get(description="train")
    option = options.get(value="daily", sub_question=train_sub_q)
    question1 = questions.get(number="1")

    response = api_client_authenticated.post(
        answer_url,
        {
            "option": option.id,
            "question": question1.id,
        },
    )
    assert response.status_code == 404
    assert Answer.objects.count() == 0


@pytest.mark.django_db
def test_answer_get_result(api_client_authenticated, users, answers):
    url = reverse("profiles:answer-get-result")
    response = api_client_authenticated.get(url)
    assert response.status_code == 200
    assert response.json()["value"] == "negative result"


@pytest.mark.django_db
def test_post_answer_where_condition_not_met(
    api_client,
    users,
    questions,
    sub_questions,
    question_conditions,
    options,
    results,
    answers,
):
    user = users.get(username="never train user")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    question3 = questions.get(number="3")
    option_easy = Option.objects.get(question=question3, value="easy")

    answer_url = reverse("profiles:answer-list")
    response = api_client.post(
        answer_url, {"option": option_easy.id, "question": question3.id}
    )
    assert response.status_code == 405


@pytest.mark.django_db
def test_post_answer_where_condition_is_met(
    api_client,
    users,
    questions,
    sub_questions,
    question_conditions,
    options,
    results,
    answers,
):
    user = users.get(username="daily train user")
    num_answers = answers.count()
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    question3 = questions.get(number="3")
    option_easy = Option.objects.get(question=question3, value="easy")

    answer_url = reverse("profiles:answer-list")
    response = api_client.post(
        answer_url, {"option": option_easy.id, "question": question3.id}
    )
    assert response.status_code == 201
    assert answers.count() == num_answers + 1
