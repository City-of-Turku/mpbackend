from unittest.mock import patch

import pytest
from django.db.models import Sum
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse

from account.models import Profile, User
from profiles.models import Answer, PostalCode, PostalCodeResult, PostalCodeType
from profiles.tests.conftest import NEG, POS

ANSWER_URL = reverse("profiles:answer-list")


@pytest.mark.django_db
def test_postal_code_result_with_postal_code_and_optional_postal_code(
    api_client, users, questions, options, results
):
    user = users.get(username="no answers user")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    Profile.objects.filter(user=user).update(
        postal_code="20210", optional_postal_code="20220"
    )
    question1 = questions.get(number="1")
    option = options.get(question=question1, value="no")
    response = api_client.post(
        ANSWER_URL, {"option": option.id, "question": question1.id}
    )
    assert response.status_code == 201
    assert Answer.objects.count() == 1
    response = api_client.post(reverse("profiles:question-end-poll"))
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 2
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code="20210")
        ).count
        == 1
    )
    assert PostalCodeResult.objects.get(
        postal_code=PostalCode.objects.get(postal_code="20210")
    ).postal_code_type == PostalCodeType.objects.get(
        type_name=PostalCodeType.HOME_POSTAL_CODE
    )
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code="20220")
        ).count
        == 1
    )
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code="20220")
        ).result.topic
        == "negative"
    )
    assert PostalCodeResult.objects.get(
        postal_code=PostalCode.objects.get(postal_code="20220")
    ).postal_code_type == PostalCodeType.objects.get(
        type_name=PostalCodeType.OPTIONAL_POSTAL_CODE
    )
    user.refresh_from_db()
    assert user.postal_code_result_saved is True


@pytest.mark.django_db
def test_postal_code_result_with_postal_code_and_without_optional_postal_code(
    api_client, users, questions, options, results
):
    user = users.get(username="no answers user")
    Profile.objects.filter(user=user).update(postal_code="20210")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    question1 = questions.get(number="1")
    option = options.get(question=question1, value="no")
    response = api_client.post(
        ANSWER_URL, {"option": option.id, "question": question1.id}
    )
    assert response.status_code == 201
    assert Answer.objects.count() == 1
    response = api_client.post(reverse("profiles:question-end-poll"))
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 2
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code=20210),
            postal_code_type=PostalCodeType.objects.get(
                type_name=PostalCodeType.HOME_POSTAL_CODE
            ),
        ).count
        == 1
    )
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code=None),
            postal_code_type=PostalCodeType.objects.get(
                type_name=PostalCodeType.OPTIONAL_POSTAL_CODE
            ),
        ).count
        == 1
    )
    user.refresh_from_db()
    assert user.postal_code_result_saved is True


@pytest.mark.django_db
def test_postal_code_result_without_postal_code_and_optional_postal_code(
    api_client, users, questions, options, results
):
    user = users.get(username="no answers user")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    question1 = questions.get(number="1")
    option = options.get(question=question1, value="no")
    response = api_client.post(
        ANSWER_URL, {"option": option.id, "question": question1.id}
    )
    assert response.status_code == 201
    assert Answer.objects.count() == 1
    response = api_client.post(reverse("profiles:question-end-poll"))
    assert response.status_code == 200
    assert PostalCodeResult.objects.count() == 2
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code=None),
            postal_code_type=PostalCodeType.objects.get(
                type_name=PostalCodeType.HOME_POSTAL_CODE
            ),
        ).count
        == 1
    )
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code=None),
            postal_code_type=PostalCodeType.objects.get(
                type_name=PostalCodeType.OPTIONAL_POSTAL_CODE
            ),
        ).count
        == 1
    )
    user.refresh_from_db()
    assert user.postal_code_result_saved is True


@pytest.mark.django_db
def test_postal_code_result(
    api_client, results_test_result, options_test_result, questions_test_result
):
    num_users = 5
    num_answers = 0
    start_poll_url = reverse("profiles:question-start-poll")
    postal_codes = [None, "20100", "20200", "20100", None]
    q1 = questions_test_result.get(number="1")
    q1_option_pos = options_test_result.get(question=q1, value=POS)
    q1_option_neg = options_test_result.get(question=q1, value=NEG)

    # post positive
    for i in range(num_users):
        response = None
        with patch("profiles.api.views.verify_recaptcha") as mock_verify_recaptcha:
            mock_verify_recaptcha.return_value = True
            response = api_client.post(start_poll_url, {"token": "token"})

        token = response.json()["token"]
        assert response.status_code == 200
        token = response.json()["token"]
        user_id = response.json()["id"]
        assert User.objects.all().count() == 1 + i
        user = User.objects.get(id=user_id)
        user.profile.postal_code = postal_codes[i]
        user.profile.optional_postal_code = postal_codes[i]
        user.profile.save()
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        api_client.post(ANSWER_URL, {"option": q1_option_pos.id, "question": q1.id})
        num_answers += 1
        assert Answer.objects.count() == num_answers
        response = api_client.post(reverse("profiles:question-end-poll"))
        api_client.credentials()
    assert PostalCodeResult.objects.count() == 6
    assert PostalCode.objects.count() == 3
    assert PostalCodeType.objects.count() == 2
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code=None),
            postal_code_type=PostalCodeType.objects.get(
                type_name=PostalCodeType.HOME_POSTAL_CODE
            ),
        ).count
        == 2
    )
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code="20100"),
            postal_code_type=PostalCodeType.objects.get(
                type_name=PostalCodeType.HOME_POSTAL_CODE
            ),
        ).count
        == 2
    )
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code="20200"),
            postal_code_type=PostalCodeType.objects.get(
                type_name=PostalCodeType.HOME_POSTAL_CODE
            ),
        ).count
        == 1
    )
    assert (
        PostalCodeResult.objects.get(
            postal_code=PostalCode.objects.get(postal_code=None),
            postal_code_type=PostalCodeType.objects.get(
                type_name=PostalCodeType.HOME_POSTAL_CODE
            ),
        ).result.topic
        == POS
    )

    # post negative, but only to user Home postal code
    for i in range(num_users):
        with patch("profiles.api.views.verify_recaptcha") as mock_verify_recaptcha:
            mock_verify_recaptcha.return_value = True
            response = api_client.post(start_poll_url, {"token": "token"})
            token = response.json()["token"]
            assert response.status_code == 200
        token = response.json()["token"]
        user_id = response.json()["id"]
        assert User.objects.all().count() == num_users + 1 + i
        user = User.objects.get(id=user_id)
        user.profile.postal_code = postal_codes[i]
        user.profile.optional_postal_code = None
        user.profile.save()
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        api_client.post(ANSWER_URL, {"option": q1_option_neg.id, "question": q1.id})
        num_answers += 1
        assert Answer.objects.count() == num_answers
        response = api_client.post(reverse("profiles:question-end-poll"))
        api_client.credentials()
    neg_result = results_test_result.get(topic=NEG)
    pos_result = results_test_result.get(topic=POS)

    assert PostalCode.objects.count() == 3
    assert PostalCodeType.objects.count() == 2
    assert PostalCodeResult.objects.count() == 10  # 6 +4
    assert PostalCodeResult.objects.filter(result=neg_result).count() == 4
    assert PostalCodeResult.objects.get(
        result=neg_result,
        postal_code_type=PostalCodeType.objects.get(
            type_name=PostalCodeType.OPTIONAL_POSTAL_CODE
        ),
    ).count == len(postal_codes)
    assert (
        PostalCodeResult.objects.get(
            result=neg_result,
            postal_code_type=PostalCodeType.objects.get(
                type_name=PostalCodeType.OPTIONAL_POSTAL_CODE
            ),
        ).result.topic
        == NEG
    )
    assert (
        PostalCodeResult.objects.filter(result=pos_result).aggregate(
            total_count=(Sum("count"))
        )["total_count"]
        == len(postal_codes) * 2
    )
    assert (
        PostalCodeResult.objects.filter(result=neg_result).aggregate(
            total_count=(Sum("count"))
        )["total_count"]
        == len(postal_codes) * 2
    )


@pytest.mark.django_db
def test_non_existing_postal_code_type(api_client):
    url = reverse("profiles:postalcoderesult-list") + "?postal_code_type=42"
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_non_existing_postal_code_type_string(api_client):
    url = reverse("profiles:postalcoderesult-list") + "?postal_code_type_string=Homer"
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_non_existing_postal_code(api_client):
    url = reverse("profiles:postalcoderesult-list") + "?postal_code=42"
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_non_existing_postal_code_string(api_client):
    url = reverse("profiles:postalcoderesult-list") + "?postal_code_string=42042"
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["count"] == 0
