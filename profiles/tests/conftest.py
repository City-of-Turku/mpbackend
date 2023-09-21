import pytest
from rest_framework.test import APIClient

from profiles.models import Option, Question, QuestionCondition, Result, SubQuestion


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.fixture
def questions():
    Question.objects.create(question="Do you use car?", number="1")
    Question.objects.create(question="How often do you use car?", number="1b")
    Question.objects.create(
        question="How often do you use following means of public transport?", number="2"
    )
    Question.objects.create(question="why do you use train?", number="3")
    return Question.objects.all()


@pytest.mark.django_db
@pytest.fixture()
def sub_questions(questions):
    question = Question.objects.get(number="2")
    SubQuestion.objects.create(question=question, description="train", order_number=0)
    SubQuestion.objects.create(question=question, description="car", order_number=1)
    return SubQuestion.objects.all()


@pytest.mark.django_db
@pytest.fixture
def options(questions, sub_questions, results):
    option_no = Option.objects.create(
        value="no", question=Question.objects.get(number="1")
    )
    option_no.results.add(Result.objects.get(value="negative result"))
    option_yes = Option.objects.create(
        value="yes", question=Question.objects.get(number="1")
    )
    option_yes.results.add(Result.objects.get(value="positive result"))

    train_sub_q = SubQuestion.objects.get(description="train")
    car_sub_q = SubQuestion.objects.get(description="car")
    Option.objects.create(value="never", sub_question=train_sub_q)
    Option.objects.create(value="daily", sub_question=train_sub_q)
    Option.objects.create(value="never", sub_question=car_sub_q)
    Option.objects.create(value="daily", sub_question=car_sub_q)
    return Option.objects.all()


@pytest.mark.django_db
@pytest.fixture
def results():
    Result.objects.create(value="negative result")
    Result.objects.create(value="positive result")
    return Result.objects.all()


@pytest.mark.django_db
@pytest.fixture
def question_conditions(questions, sub_questions, options, results):
    car_question = Question.objects.get(number="1")
    how_often_car_question = Question.objects.get(number="1b")
    how_ofter_public_transport_question = Question.objects.get(number="2")
    why_use_train_question = Question.objects.get(number="3")
    train_sub_q = SubQuestion.objects.get(description="train")
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
