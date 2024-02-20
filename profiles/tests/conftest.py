import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from account.models import Profile, User
from profiles.models import (
    Answer,
    Option,
    Question,
    QuestionCondition,
    Result,
    SubQuestion,
    SubQuestionCondition,
)

POS = "pos"
NEG = "neg"
OK = "ok"
YES_BIKE = "yes bike"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_client_authenticated(users):
    user = users.get(username="test1")
    token = Token.objects.create(user=user)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return api_client


@pytest.fixture
def api_client_auth_no_answers(users):
    user = users.get(username="no answers user")
    token = Token.objects.create(user=user)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return api_client


@pytest.fixture()
def api_client_with_custom_ip_address(ip_address):
    return APIClient(REMOTE_ADDR=ip_address)


@pytest.mark.django_db
@pytest.fixture
def questions_test_result():
    Question.objects.create(question="q1", number="1")
    Question.objects.create(question="q2", number="2")
    Question.objects.create(question="q3", number="3")
    return Question.objects.all()


@pytest.mark.django_db
@pytest.fixture
def results_test_result():
    values = [POS, OK, NEG]
    for value in values:
        Result.objects.create(topic=value, description=f"test_{value}")
    return Result.objects.all()


@pytest.mark.django_db
@pytest.fixture
def options_test_result(questions_test_result, results_test_result):
    q1 = questions_test_result.get(number="1")
    q2 = questions_test_result.get(number="2")
    q3 = questions_test_result.get(number="3")
    questions = [q1, q2, q3]
    values = [POS, OK, NEG]
    for v_c, value in enumerate(values):
        result = results_test_result.get(topic=value)
        for q_c, question in enumerate(questions):
            option = Option.objects.create(question=question, value=value)
            """
            q1 has all the results added to the options
            q2 has NEG and OK
            q3 has only NEG
            """
            if q_c <= v_c:
                option.results.add(result)

    return Option.objects.all()


@pytest.mark.django_db
@pytest.fixture
def options_with_multiple_results(questions_test_result, results_test_result):
    q3 = questions_test_result.get(number="3")
    pos_res = Result.objects.get(topic=POS)
    ok_res = Result.objects.get(topic=OK)
    option = Option.objects.create(question=q3, value=YES_BIKE)
    option.results.add(pos_res)
    option.results.add(ok_res)
    return Option.objects.all()


@pytest.mark.django_db
@pytest.fixture
def questions():
    Question.objects.create(question="Do you use car?", number="1")
    Question.objects.create(question="How often do you use car?", number="1b")
    Question.objects.create(
        question="How often do you use following means of public transport?", number="2"
    )
    Question.objects.create(question="Why do you use train?", number="3")
    Question.objects.create(question="Questions about car driving", number="4")
    return Question.objects.all()


@pytest.mark.django_db
@pytest.fixture()
def sub_questions(questions):
    question = questions.get(number="2")
    SubQuestion.objects.create(question=question, description="train", order_number=0)
    SubQuestion.objects.create(question=question, description="car", order_number=1)
    question = Question.objects.get(number="4")
    SubQuestion.objects.create(
        question=question, description="Do you drive yourself?", order_number=0
    )

    return SubQuestion.objects.all()


@pytest.mark.django_db
@pytest.fixture
def options(questions, sub_questions, results):
    positive_result = results.get(topic="positive")
    negative_result = results.get(topic="negative")
    question1 = questions.get(number="1")
    option_no = Option.objects.create(value="no", question=question1)
    option_no.results.add(negative_result)
    option_yes = Option.objects.create(value="yes", question=question1)
    option_yes.results.add(positive_result)
    train_sub_q = sub_questions.get(description="train")
    car_sub_q = sub_questions.get(description="car")
    Option.objects.create(value="never", sub_question=train_sub_q)
    Option.objects.create(value="daily", sub_question=train_sub_q)
    option_never = Option.objects.create(value="never", sub_question=car_sub_q)
    option_never.results.add(negative_result)
    option_daily = Option.objects.create(value="daily", sub_question=car_sub_q)
    option_daily.results.add(positive_result)
    question3 = Question.objects.get(number="3")
    Option.objects.create(value="fast", question=question3)
    Option.objects.create(value="easy", question=question3)
    Option.objects.create(value="other", question=question3, is_other=True)

    Option.objects.create(
        value="yes I drive",
        sub_question=SubQuestion.objects.get(description="Do you drive yourself?"),
    )
    return Option.objects.all()


@pytest.mark.django_db
@pytest.fixture
def results():
    Result.objects.create(topic="negative", description="negative result")
    Result.objects.create(topic="positive", description="positive result")
    return Result.objects.all()


@pytest.mark.django_db
@pytest.fixture
def question_conditions(questions, sub_questions, options, results):
    car_question = questions.get(number="1")
    how_often_car_question = questions.get(number="1b")
    how_ofter_public_transport_question = questions.get(number="2")
    why_use_train_question = questions.get(number="3")
    train_sub_q = sub_questions.get(description="train")
    # Set condition, if uses train daily.
    cond = QuestionCondition.objects.create(
        question=why_use_train_question,
        question_condition=how_ofter_public_transport_question,
        sub_question_condition=train_sub_q,
    )
    cond.option_conditions.add(
        Option.objects.get(sub_question=train_sub_q, value="daily")
    )
    cond = QuestionCondition.objects.create(
        question=how_often_car_question, question_condition=car_question
    )
    cond.option_conditions.add(Option.objects.get(question=car_question, value="yes"))
    return QuestionCondition.objects.all()


@pytest.mark.django_db
@pytest.fixture
def sub_question_conditions(questions, sub_questions, options):
    sub_question = sub_questions.get(description="Do you drive yourself?")
    question_condition = questions.get(question="Do you use car?")
    option_yes = options.get(value="yes", question=question_condition)
    SubQuestionCondition.objects.create(sub_question=sub_question, option=option_yes)
    return SubQuestionCondition.objects.all()


@pytest.mark.django_db
@pytest.fixture
def users():
    user = User.objects.create(username="test1")
    Profile.objects.create(user=user)
    user = User.objects.create(username="car user")
    Profile.objects.create(user=user)
    user = User.objects.create(username="non car user")
    Profile.objects.create(user=user)
    user = User.objects.create(username="daily train user")
    Profile.objects.create(user=user)
    user = User.objects.create(username="never train user")
    Profile.objects.create(user=user)
    user = User.objects.create(username="car and train user")
    Profile.objects.create(user=user)
    user = User.objects.create(username="no answers user")
    Profile.objects.create(user=user)
    return User.objects.all()


@pytest.mark.django_db
@pytest.fixture
def answers(users, questions, options, sub_questions):
    Answer.objects.create(
        user=users.get(username="test1"),
        question=questions.get(number="1"),
        option=options.get(value="no"),
    )
    Answer.objects.create(
        user=users.get(username="car user"),
        question=questions.get(number="1"),
        option=options.get(value="yes"),
    )
    Answer.objects.create(
        user=users.get(username="non car user"),
        question=questions.get(number="1"),
        option=options.get(value="no"),
    )
    # Fixtures used when testing if sub question condition is met in question
    train_sub_q = sub_questions.get(description="train")
    option_daily_train = options.get(value="daily", sub_question=train_sub_q)
    option_never_train = options.get(value="never", sub_question=train_sub_q)
    question2 = questions.get(number="2")
    Answer.objects.create(
        user=users.get(username="daily train user"),
        question=question2,
        option=option_daily_train,
    )
    Answer.objects.create(
        user=users.get(username="never train user"),
        question=question2,
        option=option_never_train,
    )

    # Fixtures to test questions_condition_states
    Answer.objects.create(
        user=users.get(username="car and train user"),
        question=questions.get(number="1"),
        option=options.get(value="yes"),
    )
    Answer.objects.create(
        user=users.get(username="car and train user"),
        question=question2,
        option=option_daily_train,
    )
    return Answer.objects.all()
