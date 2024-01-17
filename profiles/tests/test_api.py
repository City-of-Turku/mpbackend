import time

import pytest
from django.conf import settings
from django.db.models import Sum
from rest_framework.reverse import reverse

from account.models import User
from profiles.models import (
    Answer,
    Option,
    PostalCode,
    PostalCodeResult,
    PostalCodeType,
    Question,
    Result,
    SubQuestion,
)


@pytest.mark.django_db
def test_postal_code_result(
    api_client, questions, sub_questions, question_conditions, options, results
):
    num_users = 21
    num_answers = 0
    start_poll_url = reverse("profiles:question-start-poll")
    end_poll_url = reverse("profiles:question-end-poll")
    answer_url = reverse("profiles:answer-list")
    positive_result = Result.objects.get(value="positive result")
    negative_result = Result.objects.get(value="negative result")
    question1 = Question.objects.get(number="1")
    question2 = Question.objects.get(number="2")
    car_sub_q = SubQuestion.objects.get(question=question2, description="car")
    car_sub_q_options = Option.objects.filter(sub_question=car_sub_q)
    q1_options = Option.objects.filter(question=question1)
    questions = {question1: q1_options, car_sub_q: car_sub_q_options}
    postal_codes = [None, "20100", "20200", "20210", "20100"]
    postal_code_types = [
        None,
        PostalCodeType.HOME_POSTAL_CODE,
        PostalCodeType.HOME_POSTAL_CODE,
        PostalCodeType.OPTIONAL_POSTAL_CODE,
        PostalCodeType.OPTIONAL_POSTAL_CODE,
    ]

    for i in range(num_users):
        start_poll_url = reverse("profiles:question-start-poll")
        response = api_client.post(start_poll_url)
        assert response.status_code == 200
        user_id = response.json()["id"]
        User.objects.all().count() == 1 + i
        user = User.objects.get(id=user_id)
        index = i % 5
        postal_code_location = postal_code_types[index]
        if postal_code_location == PostalCodeType.HOME_POSTAL_CODE:
            user.profile.postal_code = postal_codes[index]
        elif postal_code_location == PostalCodeType.OPTIONAL_POSTAL_CODE:
            user.profile.optional_postal_code = postal_codes[index]
        user.profile.save()
        # negative options(answer) has index 0, positive 1 in fixure opiton querysets
        # negative are no/never and positive are yes/daily
        # Make 2/3 of answers negative
        if i % 3 < 2:
            option_index = 0
        else:
            option_index = 1
        for q_item in questions.items():
            body = {"option": q_item[1][option_index].id}
            if isinstance(q_item[0], SubQuestion):
                body["sub_question"] = q_item[0].id
                body["question"] = q_item[0].question.id
            else:
                body["question"] = q_item[0].id

            response = api_client.post(answer_url, body)
            num_answers += 1
            assert Answer.objects.count() == num_answers

        user = User.objects.get(id=user_id)
        if option_index == 0:
            assert user.result == negative_result
        else:
            assert user.result == positive_result

        response = api_client.post(end_poll_url)
        assert response.status_code == 200
        user = User.objects.get(id=user_id)
        assert user.postal_code_result_saved is True

    # Note 20100 is both a Home and Optional postal code
    assert PostalCode.objects.count() == 3
    # 2 * 5    number of different results * absolute(home and optional) number of postal codes
    assert PostalCodeResult.objects.count() == 10
    # A count should be added for every user that answers and ends the poll
    assert (
        PostalCodeResult.objects.aggregate(total_count=(Sum("count")))["total_count"]
        == num_users
    )
    num_positive_results = PostalCodeResult.objects.filter(
        result=positive_result
    ).aggregate(total_count=(Sum("count")))["total_count"]
    num_negative_results = PostalCodeResult.objects.filter(
        result=negative_result
    ).aggregate(total_count=(Sum("count")))["total_count"]
    # 1/3 of the results are negative
    assert num_negative_results == pytest.approx(num_users * (1 / 3), 1)
    # 2/3 are positive
    assert num_positive_results == pytest.approx(num_users * (2 / 3), 1)

    url = reverse("profiles:postalcoderesult-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["count"] == 10
    postal_code_20100 = PostalCode.objects.get(postal_code=20100)
    url = (
        reverse("profiles:postalcoderesult-list")
        + f"?postal_code={postal_code_20100.id}"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 4
    postal_code_type_home = PostalCodeType.objects.get(
        type_name=PostalCodeType.HOME_POSTAL_CODE
    )
    url = (
        reverse("profiles:postalcoderesult-list")
        + f"?postal_code_type={postal_code_type_home.id}"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 4
    url = (
        reverse("profiles:postalcoderesult-list")
        + f"?postal_code_type={postal_code_type_home.id}&postal_code={postal_code_20100.id}"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 2
    url = reverse("profiles:postalcoderesult-list") + "?postal_code_type="
    response = api_client.get(url)
    assert response.json()["count"] == 2
    url = reverse("profiles:postalcoderesult-list") + "?postal_code_type=&postal_code="
    response = api_client.get(url)
    assert response.json()["count"] == 2
    # Test nonexisting postal code type
    url = reverse("profiles:postalcoderesult-list") + "?postal_code_type=42"
    response = api_client.get(url)
    # Test nonexisting postal code
    url = reverse("profiles:postalcoderesult-list") + "?postal_code=42"
    response = api_client.get(url)
    assert response.status_code == 404


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
    response = api_client.post(
        answer_url, {"option": option.id, "question": question1.id}
    )
    assert Answer.objects.count() == 1
    user = User.objects.first()
    assert user.result.value == "negative result"
    # Answer to sub question
    how_ofter_public_transport_question = Question.objects.get(number="2")
    train_sub_q = SubQuestion.objects.get(
        question=how_ofter_public_transport_question, description="train"
    )
    option = Option.objects.get(sub_question=train_sub_q, value="daily")
    response = api_client.post(
        answer_url,
        {
            "option": option.id,
            "question": how_ofter_public_transport_question.id,
            "sub_question": train_sub_q.id,
        },
    )
    assert Answer.objects.count() == 2
    assert Answer.objects.filter(user=user).last().option == option
    # Test post answer with erroneous question id, not related to option
    response = api_client.post(
        answer_url,
        {
            "option": option.id,
            "question": question1.id,
        },
    )
    assert response.status_code == 404
    assert Answer.objects.count() == 2
    # Test get-result endpoint
    url = reverse("profiles:answer-get-result")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["value"] == "negative result"
    # Test test_condition endpoint
    # car not used, so the condition is not met
    condition_url = reverse("profiles:question-check-if-question-condition-met")
    response = api_client.post(
        condition_url, {"question": Question.objects.get(number="1b").id}
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is False
    question1 = Question.objects.get(number="1")
    option = Option.objects.get(question=question1, value="yes")
    response = api_client.post(
        answer_url, {"option": option.id, "question": question1.id}
    )
    # previous answer should be updated
    assert Answer.objects.count() == 2
    # 'yes' answered to car usage and the condition is met
    response = api_client.post(
        condition_url, {"question": Question.objects.get(number="1b").id}
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is True

    # sub_queston train is answered with 'daily' so the condition is met
    question3 = Question.objects.get(number="3")
    response = api_client.post(condition_url, {"question": question3.id})
    assert response.status_code == 200
    assert response.json()["condition_met"] is True
    # Change answer to never
    option = Option.objects.get(sub_question=train_sub_q, value="never")
    response = api_client.post(
        answer_url,
        {
            "option": option.id,
            "question": how_ofter_public_transport_question.id,
            "sub_question": train_sub_q.id,
        },
    )
    assert Answer.objects.count() == 2
    # sub_queston train is answered with 'never' so the condition is Not met
    response = api_client.post(condition_url, {"question": question3.id})
    assert response.status_code == 200
    assert response.json()["condition_met"] is False

    # Test that posting answer to a question where condition is not met fails
    # As train sub_question is answered with "never", the condition
    # for question "why do you use train?" is not met.
    option_easy = Option.objects.get(question=question3, value="easy")
    response = api_client.post(
        answer_url, {"option": option_easy.id, "question": question3.id}
    )
    assert response.status_code == 405
    # Change answer to "daily", therefore to condition for question3 is met
    option = Option.objects.get(sub_question=train_sub_q, value="daily")
    response = api_client.post(
        answer_url,
        {
            "option": option.id,
            "question": how_ofter_public_transport_question.id,
            "sub_question": train_sub_q.id,
        },
    )
    response = api_client.post(
        answer_url, {"option": option_easy.id, "question": question3.id}
    )
    assert response.status_code == 201
    assert Answer.objects.count() == 3

    # Test 'in_condition' endpoint
    # 1b question is not incondition
    in_condition_url = reverse("profiles:question-in-condition")
    response = api_client.post(
        in_condition_url, {"question": Question.objects.get(number="1b").id}
    )
    assert response.status_code == 200
    assert response.json()["in_condition"] is False
    # Question 1 is in condition
    response = api_client.post(
        in_condition_url, {"question": Question.objects.get(number="1").id}
    )
    assert response.status_code == 200
    assert response.json()["in_condition"] is True
    # Test end poll (logout)
    url = reverse("profiles:question-end-poll")
    response = api_client.post(url)
    assert response.status_code == 200
    url = reverse("profiles:answer-list")
    # should return 403 Forbidden as end_poll has logged out the user
    response = api_client.post(url, {"option": option.id})
    assert response.status_code == 403


@pytest.mark.django_db
def test_sub_question_condition(
    api_client, questions, sub_question_conditions, options, sub_questions
):
    url = reverse("profiles:question-start-poll")
    response = api_client.post(url)
    assert response.status_code == 200
    answer_url = reverse("profiles:answer-list")
    question_condition = Question.objects.get(question="Do you use car?")
    driving_question = Question.objects.get(question="Questions about car driving")
    sub_question = SubQuestion.objects.get(description="Do you drive yourself?")

    option_yes = Option.objects.get(value="yes", question=question_condition)
    option_yes_i_drive = Option.objects.get(
        value="yes I drive", sub_question=sub_question
    )
    option_no = Option.objects.get(value="no", question=question_condition)

    response = api_client.post(
        answer_url,
        {
            "option": option_yes.id,
            "question": question_condition.id,
        },
    )
    assert response.status_code == 201

    condition_url = reverse("profiles:question-check-if-sub-question-condition-met")
    response = api_client.post(
        condition_url,
        {
            "sub_question": SubQuestion.objects.get(
                description="Do you drive yourself?"
            ).id
        },
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is True
    # Now the condition is met ,so answering the question should return code 201
    response = api_client.post(
        answer_url,
        {
            "option": option_yes_i_drive.id,
            "question": driving_question.id,
            "sub_question": sub_question.id,
        },
    )
    assert response.status_code == 201

    response = api_client.post(
        answer_url,
        {
            "option": option_no.id,
            "question": question_condition.id,
        },
    )
    assert response.status_code == 201
    assert Answer.objects.all().count() == 2
    response = api_client.post(
        condition_url,
        {
            "sub_question": SubQuestion.objects.get(
                description="Do you drive yourself?"
            ).id
        },
    )
    assert response.status_code == 200
    assert response.json()["condition_met"] is False

    response = api_client.post(
        answer_url,
        {
            "option": option_no.id,
            "question": question_condition.id,
        },
    )
    assert response.status_code == 201
    assert Answer.objects.all().count() == 2
    # Now the condition is Not met, so answering the question should return code 405
    response = api_client.post(
        answer_url,
        {
            "option": option_yes_i_drive.id,
            "question": driving_question.id,
            "sub_question": sub_question.id,
        },
    )
    assert response.status_code == 405
    assert Answer.objects.all().count() == 2


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
    api_client_with_custom_ip_address.force_login(user=users.first())
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


@pytest.mark.django_db
def test_result_count_is_filled_for_fun_is_false(api_client, answers, users):
    user = users.first()
    api_client.force_login(user=user)
    assert user.profile.is_filled_for_fun is False
    url = reverse("profiles:question-end-poll")
    response = api_client.post(url)
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 1


@pytest.mark.django_db
def test_result_count_is_filled_for_fun_is_true(api_client, answers, users):
    user = users.first()
    api_client.force_login(user=user)
    url = reverse("profiles:question-end-poll")
    user.profile.is_filled_for_fun = True
    user.profile.save()
    response = api_client.post(url)
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 0


@pytest.mark.django_db
def test_result_count_result_can_be_used_is_true(api_client, answers, users):
    user = users.first()
    api_client.force_login(user=user)
    assert user.profile.result_can_be_used is True
    url = reverse("profiles:question-end-poll")
    response = api_client.post(url)
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 1


@pytest.mark.django_db
def test_result_count_result_can_be_used_is_false(api_client, answers, users):
    user = users.first()
    api_client.force_login(user=user)
    user.profile.result_can_be_used = False
    user.profile.save()
    url = reverse("profiles:question-end-poll")
    response = api_client.post(url)
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 0
