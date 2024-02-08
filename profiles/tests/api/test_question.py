import time

import pytest
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse

from profiles.models import Answer, PostalCodeResult


@pytest.mark.django_db
@pytest.mark.django_db
def test_sub_questions_conditions_states(
    api_client,
    users,
    answers,
    questions,
    question_conditions,
    sub_questions,
    sub_question_conditions,
):
    url = reverse("profiles:question-get-sub-questions-conditions-states")
    user = users.get(username="car user")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()[0]["state"] is True
    user = users.get(username="non car user")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    response = api_client.get(url)
    assert response.json()[0]["state"] is False


@pytest.mark.django_db
def test_questions_condition_states_not_authenticated(
    api_client, users, questions, question_conditions
):
    url = reverse("profiles:question-get-questions-conditions-states")
    response = api_client.get(url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_questions_condition_states(
    api_client, users, answers, questions, question_conditions
):
    user = users.get(username="car user")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    url = reverse("profiles:question-get-questions-conditions-states")
    response = api_client.get(url)
    assert response.status_code == 200
    how_often_car_question = questions.get(number="1b")
    why_use_train_question = questions.get(number="3")

    assert response.json()[0]["id"] == how_often_car_question.id
    assert response.json()[0]["state"] is True
    assert response.json()[1]["id"] == why_use_train_question.id
    assert response.json()[1]["state"] is False

    user = users.get(username="non car user")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    url = reverse("profiles:question-get-questions-conditions-states")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()[0]["id"] == how_often_car_question.id
    assert response.json()[0]["state"] is False
    assert response.json()[1]["id"] == why_use_train_question.id
    assert response.json()[1]["state"] is False

    user = users.get(username="car and train user")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    url = reverse("profiles:question-get-questions-conditions-states")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()[0]["id"] == how_often_car_question.id
    assert response.json()[0]["state"] is True
    assert response.json()[1]["id"] == why_use_train_question.id
    assert response.json()[1]["state"] is True


@pytest.mark.django_db
def test_get_questions_with_conditions(
    api_client, users, answers, questions, question_conditions
):
    url = reverse("profiles:question-get-questions-with-conditions")
    response = api_client.get(url)
    json_data = response.json()
    assert json_data["count"] == 2
    assert json_data["results"][0]["number"] == "1b"
    assert json_data["results"][1]["number"] == "3"


@pytest.mark.django_db
def test_question_condition_is_met(
    api_client, users, answers, questions, question_conditions
):
    user = users.get(username="car user")
    token = Token.objects.create(user=user)
    condition_url = reverse("profiles:question-check-if-question-condition-met")
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    response = api_client.post(
        condition_url, {"question": questions.get(number="1b").id}
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is True


@pytest.mark.django_db
def test_question_condition_not_met(
    api_client, users, answers, questions, question_conditions
):
    user = users.get(username="non car user")
    token = Token.objects.create(user=user)
    condition_url = reverse("profiles:question-check-if-question-condition-met")
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    response = api_client.post(
        condition_url, {"question": questions.get(number="1b").id}
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is False


@pytest.mark.django_db
def test_question_with_sub_question_condition_is_met(
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
    token = Token.objects.create(user=user)
    condition_url = reverse("profiles:question-check-if-question-condition-met")
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    response = api_client.post(
        condition_url, {"question": questions.get(number="3").id}
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is True


@pytest.mark.django_db
def test_question_with_sub_question_condition_not_met(
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
    condition_url = reverse("profiles:question-check-if-question-condition-met")
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    response = api_client.post(
        condition_url, {"question": questions.get(number="3").id}
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is False


@pytest.mark.django_db
def test_question_not_in_condition(
    api_client_authenticated, questions, question_conditions
):
    # 1b question is not in condition
    in_condition_url = reverse("profiles:question-in-condition")
    response = api_client_authenticated.post(
        in_condition_url, {"question": questions.get(number="1b").id}
    )
    assert response.status_code == 200
    assert response.json()["in_condition"] is False


@pytest.mark.django_db
def test_question_in_condition(
    api_client_authenticated, questions, question_conditions
):
    # question 1 is in condition
    in_condition_url = reverse("profiles:question-in-condition")
    response = api_client_authenticated.post(
        in_condition_url, {"question": questions.get(number="1").id}
    )
    assert response.status_code == 200
    assert response.json()["in_condition"] is True


@pytest.mark.django_db
def test_end_poll(api_client_authenticated, questions, options):
    url = reverse("profiles:question-end-poll")
    response = api_client_authenticated.post(url)
    assert response.status_code == 200
    url = reverse("profiles:answer-list")
    response = api_client_authenticated.post(
        url,
        {
            "option": options.get(value="yes").id,
            "question": questions.get(number="1").id,
        },
    )
    assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ip_address",
    [
        ("192.168.1.41"),
    ],
)
def test_questions_anon_throttling(api_client_with_custom_ip_address):
    count = 0
    url = reverse("profiles:question-list")
    num_requests = int(
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon"].split("/")[0]
    )
    while count < num_requests:
        response = api_client_with_custom_ip_address.get(url)
        assert response.status_code == 200
        count += 1
    time.sleep(2)
    response = api_client_with_custom_ip_address.get(url)
    assert response.status_code == 429


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ip_address",
    [
        ("192.168.1.42"),
    ],
)
def test_questions_user_throttling(api_client_with_custom_ip_address, users):
    user = users.get(username="test1")
    token = Token.objects.create(user=user)

    api_client_with_custom_ip_address.credentials(
        HTTP_AUTHORIZATION="Token " + token.key
    )
    count = 0
    url = reverse("profiles:question-list")
    num_requests = int(
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user"].split("/")[0]
    )
    while count < num_requests:
        response = api_client_with_custom_ip_address.get(url)
        assert response.status_code == 200
        count += 1
    time.sleep(2)
    response = api_client_with_custom_ip_address.get(url)
    assert response.status_code == 429


@pytest.mark.django_db
def test_question_list(api_client, questions):
    url = reverse("profiles:question-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.json()["results"]) == questions.count()


@pytest.mark.django_db
def test_questions(api_client, questions, question_conditions, options, results):
    question = questions.first()
    url = reverse("profiles:question-detail", args=[str(question.id)])
    response = api_client.get(url)
    assert response.status_code == 200
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


@pytest.mark.django_db
def test_get_question_by_number(api_client, questions):
    url = reverse("profiles:question-get-question") + "?number=2"
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["question"] == questions.filter(number=2).first().question


@pytest.mark.django_db
def test_get_non_existing_question_by_number(api_client, questions):
    url = reverse("profiles:question-get-question") + "?number=2222"
    response = api_client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_get_question_by_numbers(api_client, questions):
    url = reverse("profiles:question-get-question-numbers")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["results"][-1]["number"] == questions.last().number


@pytest.mark.django_db
def test_result_count_is_filled_for_fun_is_false(
    api_client_authenticated, answers, users
):
    user = users.get(username="test1")
    assert user.profile.is_filled_for_fun is False
    url = reverse("profiles:question-end-poll")
    response = api_client_authenticated.post(url)
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 1


@pytest.mark.django_db
def test_result_count_is_filled_for_fun_is_true(
    api_client_authenticated, answers, users
):
    user = users.get(username="test1")
    url = reverse("profiles:question-end-poll")
    user.profile.is_filled_for_fun = True
    user.profile.save()
    response = api_client_authenticated.post(url)
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 0


@pytest.mark.django_db
def test_result_count_result_can_be_used_is_true(
    api_client_authenticated, answers, users
):
    user = users.get(username="test1")
    assert user.profile.result_can_be_used is True
    url = reverse("profiles:question-end-poll")
    response = api_client_authenticated.post(url)
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 1


@pytest.mark.django_db
def test_result_count_result_can_be_used_is_false(
    api_client_authenticated, answers, users
):
    user = users.get(username="test1")
    user.profile.result_can_be_used = False
    user.profile.save()
    url = reverse("profiles:question-end-poll")
    response = api_client_authenticated.post(url)
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 0


@pytest.mark.django_db
def test_sub_question_condition(
    api_client_authenticated, questions, sub_question_conditions, options, sub_questions
):
    url = reverse("profiles:question-start-poll")
    response = api_client_authenticated.post(url)
    assert response.status_code == 200
    answer_url = reverse("profiles:answer-list")
    question_condition = questions.get(question="Do you use car?")
    driving_question = questions.get(question="Questions about car driving")
    sub_question = sub_questions.get(description="Do you drive yourself?")

    option_yes = options.get(value="yes", question=question_condition)
    option_yes_i_drive = options.get(value="yes I drive", sub_question=sub_question)
    option_no = options.get(value="no", question=question_condition)

    response = api_client_authenticated.post(
        answer_url,
        {
            "option": option_yes.id,
            "question": question_condition.id,
        },
    )
    assert response.status_code == 201

    condition_url = reverse("profiles:question-check-if-sub-question-condition-met")
    response = api_client_authenticated.post(
        condition_url,
        {"sub_question": sub_questions.get(description="Do you drive yourself?").id},
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is True
    # Now the condition is met ,so answering the question should return code 201
    response = api_client_authenticated.post(
        answer_url,
        {
            "option": option_yes_i_drive.id,
            "question": driving_question.id,
            "sub_question": sub_question.id,
        },
    )
    assert response.status_code == 201

    response = api_client_authenticated.post(
        answer_url,
        {
            "option": option_no.id,
            "question": question_condition.id,
        },
    )
    assert response.status_code == 201
    assert Answer.objects.all().count() == 2
    response = api_client_authenticated.post(
        condition_url,
        {"sub_question": sub_questions.get(description="Do you drive yourself?").id},
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is False

    response = api_client_authenticated.post(
        answer_url,
        {
            "option": option_no.id,
            "question": question_condition.id,
        },
    )
    assert response.status_code == 201
    assert Answer.objects.all().count() == 2
    # Now the condition is Not met, so answering the question should return code 405
    response = api_client_authenticated.post(
        answer_url,
        {
            "option": option_yes_i_drive.id,
            "question": driving_question.id,
            "sub_question": sub_question.id,
        },
    )
    assert response.status_code == 405
    assert Answer.objects.all().count() == 2
