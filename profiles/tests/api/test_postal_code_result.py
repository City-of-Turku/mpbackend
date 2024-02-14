import pytest
from django.db.models import Sum
from rest_framework.reverse import reverse

from account.models import User
from profiles.models import (
    Answer,
    PostalCode,
    PostalCodeResult,
    PostalCodeType,
    SubQuestion,
)


@pytest.mark.django_db
def test_postal_code_result(api_client, questions, sub_questions, options, results):
    num_users = 21
    num_answers = 0
    start_poll_url = reverse("profiles:question-start-poll")
    end_poll_url = reverse("profiles:question-end-poll")
    answer_url = reverse("profiles:answer-list")
    positive_result = results.get(topic="positive")
    negative_result = results.get(topic="negative")
    question1 = questions.get(number="1")
    question2 = questions.get(number="2")
    car_sub_q = sub_questions.get(question=question2, description="car")
    car_sub_q_options = options.filter(sub_question=car_sub_q)
    q1_options = options.filter(question=question1)
    questions = {question1: q1_options, car_sub_q: car_sub_q_options}
    postal_codes = [None, "20100", "20200", "20210", "20100"]
    postal_code_types = [
        None,
        PostalCodeType.HOME_POSTAL_CODE,
        PostalCodeType.HOME_POSTAL_CODE,
        PostalCodeType.OPTIONAL_POSTAL_CODE,
        PostalCodeType.OPTIONAL_POSTAL_CODE,
    ]
    start_poll_url = reverse("profiles:question-start-poll")
    for i in range(num_users):
        response = api_client.post(start_poll_url)
        assert response.status_code == 200

        token = response.json()["token"]
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
        # negative options(answer) has index 0, positive 1 in fixures
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

            api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
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
        api_client.credentials()

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
    url = (
        reverse("profiles:postalcoderesult-list")
        + f"?postal_code_string={postal_code_20100.postal_code}"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 4
    url = (
        reverse("profiles:postalcoderesult-list")
        + f"?postal_code_type_string={PostalCodeType.HOME_POSTAL_CODE}"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 4


@pytest.mark.django_db
def test_non_existing_postal_code_type(api_client):
    url = reverse("profiles:postalcoderesult-list") + "?postal_code_type=42"
    response = api_client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_non_existing_postal_code_type_string(api_client):
    url = reverse("profiles:postalcoderesult-list") + "?postal_code_type_string=Homer"
    response = api_client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_non_existing_postal_code(api_client):
    url = reverse("profiles:postalcoderesult-list") + "?postal_code=42"
    response = api_client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_non_existing_postal_code_string(api_client):
    url = reverse("profiles:postalcoderesult-list") + "?postal_code_string=42042"
    response = api_client.get(url)
    assert response.status_code == 404
