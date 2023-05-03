import pytest
from rest_framework.test import APIClient

from profiles.models import Option, Question, Result


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.fixture
def questions():
    Question.objects.create(question="Do you use car?")
    return Question.objects.all()


@pytest.mark.django_db
@pytest.fixture
def options(questions, results):
    option_no = Option.objects.create(value="no", question=Question.objects.first())
    option_no.results.add(Result.objects.get(value="negative result"))
    option_yes = Option.objects.create(value="yes", question=Question.objects.first())
    option_yes.results.add(Result.objects.get(value="positive result"))
    return Option.objects.all()


@pytest.mark.django_db
@pytest.fixture
def results():
    Result.objects.create(value="negative result")
    Result.objects.create(value="positive result")
    return Result.objects.all()
