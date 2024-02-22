import pytest
from rest_framework.reverse import reverse

from profiles.tests.conftest import NEG, OK, POS, YES_BIKE
from profiles.tests.utils import delete_memoized_functions_cache

ANSWER_URL = reverse("profiles:answer-list")
RESULT_URL = reverse("profiles:answer-get-result")


@pytest.mark.django_db
def test_result_no_answers(api_client_auth_no_answers):
    response = api_client_auth_no_answers.get(RESULT_URL)
    assert response.status_code == 400


@pytest.mark.django_db
@delete_memoized_functions_cache
def test_relative_result(
    api_client_auth_no_answers,
    questions_test_result,
    options_test_result,
    results_test_result,
):
    q1 = questions_test_result.get(number="1")
    q1_option_pos = options_test_result.get(question=q1, value=POS)
    api_client_auth_no_answers.post(
        ANSWER_URL, {"option": q1_option_pos.id, "question": q1.id}
    )
    q2 = questions_test_result.get(number="2")
    q2_option_ok = options_test_result.get(question=q2, value=OK)
    api_client_auth_no_answers.post(
        ANSWER_URL, {"option": q2_option_ok.id, "question": q2.id}
    )
    response = api_client_auth_no_answers.get(RESULT_URL)
    assert response.status_code == 200
    # As POS result is added to only one result and OK to two
    # the relative result is POS
    assert response.json()["topic"] == POS


@pytest.mark.django_db
@delete_memoized_functions_cache
def test_neg_result(
    api_client_auth_no_answers,
    questions_test_result,
    options_test_result,
    results_test_result,
):
    # Answer POS to q2 and q3 as they do not have the POS result added to the option
    q2 = questions_test_result.get(number="2")
    q2_option_pos = options_test_result.get(question=q2, value=POS)
    api_client_auth_no_answers.post(
        ANSWER_URL, {"option": q2_option_pos.id, "question": q2.id}
    )
    q3 = questions_test_result.get(number="3")
    q3_option_pos = options_test_result.get(question=q3, value=POS)
    api_client_auth_no_answers.post(
        ANSWER_URL, {"option": q3_option_pos.id, "question": q3.id}
    )
    # Post NEG answer
    q1 = questions_test_result.get(number="1")
    q1_option_neg = options_test_result.get(question=q1, value=NEG)
    api_client_auth_no_answers.post(
        ANSWER_URL, {"option": q1_option_neg.id, "question": q1.id}
    )
    response = api_client_auth_no_answers.get(RESULT_URL)
    assert response.json()["topic"] == NEG


@pytest.mark.django_db
@delete_memoized_functions_cache
def test_ok_result(
    api_client_auth_no_answers,
    questions_test_result,
    options_test_result,
    results_test_result,
):
    q3 = questions_test_result.get(number="3")
    q3_option_neg = options_test_result.get(question=q3, value=NEG)
    api_client_auth_no_answers.post(
        ANSWER_URL, {"option": q3_option_neg.id, "question": q3.id}
    )
    response = api_client_auth_no_answers.get(RESULT_URL)
    assert response.json()["topic"] == NEG

    q1 = questions_test_result.get(number="1")
    q1_option_ok = options_test_result.get(question=q1, value=OK)
    api_client_auth_no_answers.post(
        ANSWER_URL, {"option": q1_option_ok.id, "question": q1.id}
    )
    response = api_client_auth_no_answers.get(RESULT_URL)
    q2 = questions_test_result.get(number="2")
    q2_option_ok = options_test_result.get(question=q2, value=OK)
    api_client_auth_no_answers.post(
        ANSWER_URL, {"option": q2_option_ok.id, "question": q2.id}
    )
    response = api_client_auth_no_answers.get(RESULT_URL)
    assert response.json()["topic"] == OK


@pytest.mark.django_db
@delete_memoized_functions_cache
def test_pos_result(
    api_client_auth_no_answers,
    questions_test_result,
    options_test_result,
    results_test_result,
):
    q1 = questions_test_result.get(number="1")
    q1_option_pos = options_test_result.get(question=q1, value=POS)
    api_client_auth_no_answers.post(
        ANSWER_URL, {"option": q1_option_pos.id, "question": q1.id}
    )
    response = api_client_auth_no_answers.get(RESULT_URL)
    assert response.json()["topic"] == POS


@pytest.mark.django_db
@delete_memoized_functions_cache
def test_options_with_multiple_results(
    api_client_auth_no_answers,
    questions_test_result,
    options_test_result,
    options_with_multiple_results,
    results_test_result,
):
    q1 = questions_test_result.get(number="1")
    q1_option_ok = options_test_result.get(question=q1, value=OK)
    api_client_auth_no_answers.post(
        ANSWER_URL, {"option": q1_option_ok.id, "question": q1.id}
    )

    q3 = questions_test_result.get(number="3")
    q3_option_yes_bike = options_with_multiple_results.get(question=q3, value=YES_BIKE)
    api_client_auth_no_answers.post(
        ANSWER_URL, {"option": q3_option_yes_bike.id, "question": q3.id}
    )
    response = api_client_auth_no_answers.get(RESULT_URL)
    assert response.json()["topic"] == OK
