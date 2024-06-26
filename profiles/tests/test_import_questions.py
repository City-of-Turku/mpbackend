from io import StringIO

import pytest
from django.core.management import call_command

from profiles.management.commands.import_questions import SKIP_QUESTIONS
from profiles.models import (
    Option,
    Question,
    QuestionCondition,
    Result,
    SubQuestion,
    SubQuestionCondition,
)


def import_command(*args, **kwargs):
    out = StringIO()
    call_command(
        "import_questions",
        *args,
        stdout=out,
        stderr=StringIO(),
        **kwargs,
    )
    return out.getvalue()


@pytest.mark.django_db
def test_import_questions():
    import_command()
    # Test result animals
    results_qs = Result.objects.all()
    assert results_qs.count() == 6
    autoilija = Result.objects.get(topic_fi="Autoilija")
    assert results_qs[0].topic_fi == autoilija.topic_fi
    assert "Enkel" in results_qs[0].value_sv
    assert "You know where" in results_qs[1].description_en
    assert "Fotgängare" in results_qs[2].topic_sv
    assert results_qs[3].topic_en == "Public transport passenger"
    assert "Maas" in results_qs[4].topic_fi
    assert "Kauris" in results_qs[4].value_fi
    assert "Hjort" in results_qs[4].value_sv
    assert "Deer" in results_qs[4].value_en
    assert results_qs[0].num_options == 39
    assert results_qs[1].num_options == 45
    assert results_qs[2].num_options == 39
    assert results_qs[3].num_options == 37
    assert results_qs[4].num_options == 57
    assert results_qs[5].num_options == 64

    # Test questions
    assert Question.objects.count() == 17
    # Test question without sub questions
    question1b1 = Question.objects.get(number="1b1")
    assert question1b1.question_fi == "Miksi et koskaan kulje autolla?"
    assert question1b1.number_of_options_to_choose == "+"
    # Test Sub questions
    question1 = Question.objects.get(number="1")
    assert question1.num_sub_questions == 8
    assert question1.number_of_options_to_choose == "1"
    assert question1.description_en[0:2] == "If"
    sub_q_qs = SubQuestion.objects.filter(question=question1)
    assert sub_q_qs.count() == 8
    sq_auto = sub_q_qs.get(order_number=0)
    assert sq_auto.description_en == "Car"
    assert Option.objects.filter(sub_question=sq_auto).count() == 5
    sq_auto_1_3 = Option.objects.get(sub_question=sq_auto, order_number=3)
    assert sq_auto_1_3.value == "1-3 kertaa viikossa"
    sq_auto_4_5_results = sq_auto_1_3.results.all()
    assert sq_auto_4_5_results.count() == 2
    assert sq_auto_4_5_results[0] == autoilija
    assert sq_auto_4_5_results[1].topic_en == "Habit traveler"

    assert Question.objects.get(number="5").options.count() == 20

    sq_walk = sub_q_qs.get(order_number=6)
    sq_walk.description_sv == "Gående"
    assert Option.objects.filter(sub_question=sq_walk).count() == 5
    assert (
        Option.objects.get(sub_question=sq_walk, order_number=1).value
        == "harvemmin kuin kerran kuussa"
    )
    question1d = Question.objects.get(number="1d")
    assert question1d.num_sub_questions == 0
    assert Option.objects.filter(question=question1d).count() == 3
    assert Option.objects.get(question=question1d, order_number=1).value == "Joskus"

    question4 = Question.objects.get(number="4")
    assert question4.mandatory_number_of_sub_questions_to_answer == "*"
    assert SubQuestion.objects.filter(question=question4).count() == 7
    joukkoliikenne = SubQuestion.objects.get(question=question4, order_number=2)
    assert (
        joukkoliikenne.additional_description
        == "Tärkein syy, miksi käytän joukkoliikennettä on:"
    )
    assert Option.objects.filter(sub_question=joukkoliikenne).count() == 12
    option_saa = Option.objects.get(sub_question=joukkoliikenne, order_number=3)
    assert option_saa.value == "Säätila (sade, tuuli, jne.)."
    option_saa_results = option_saa.results.all()
    assert option_saa_results.count() == 3
    assert option_saa_results[0].topic_fi == "Joukkoliikenteen käyttäjä"
    assert option_saa_results[1].topic_sv == "MaaS-resenär"
    assert option_saa_results[2].topic_en == "Conscious traveler"

    question10 = Question.objects.get(number="10")
    option_joka_kerta = Option.objects.get(question=question10, order_number=0)
    option_joka_kerta_results = option_joka_kerta.results.all()
    assert option_joka_kerta_results.count() == 4
    assert "Autoilija" in option_joka_kerta_results[0].topic_fi
    assert "Tavan mukaan" in option_joka_kerta_results[1].topic_fi
    assert "Maas" in option_joka_kerta_results[2].topic_fi
    assert "Valveutunut" in option_joka_kerta_results[3].topic_fi

    # Test SubQuestion conditions
    sub_question_condition = SubQuestionCondition.objects.get(
        sub_question=joukkoliikenne
    )
    assert sub_question_condition.option == Option.objects.get(value_fi="Linja-autolla")

    question8 = Question.objects.get(number="8")
    assert question8.options.count() == 5
    assert question8.options.all().order_by("id")[4].value_en == "Other"
    # Test question condition
    assert QuestionCondition.objects.all().count() == 9
    conditions = QuestionCondition.objects.filter(question=question8)
    assert conditions.count() == 1
    condition_qs = QuestionCondition.objects.filter(
        question_condition=question1, sub_question_condition=sq_auto
    )
    assert condition_qs.count() == 3
    condition = QuestionCondition.objects.get(
        question=Question.objects.get(number="1a"),
        question_condition=question1,
        sub_question_condition=sq_auto,
    )
    assert condition.option_conditions.count() == 4
    assert condition.option_conditions.all()[0].value == "harvemmin kuin kerran kuussa"
    assert (
        condition.option_conditions.all()[3].value == "päivittäin tai lähes päivittäin"
    )
    assert Question.objects.get(number=16).options.count() == 5
    for number in SKIP_QUESTIONS:
        assert Question.objects.filter(number=number).count() == 0
    # Test other options
    other_options_qs = Option.objects.filter(is_other=True)
    assert other_options_qs.count() == 17
    # Test has matched "//Other"
    assert (
        other_options_qs.filter(question=Question.objects.get(number="1a")).exists()
        is True
    )
    # Test has matched "//Something else"
    assert (
        other_options_qs.filter(question=Question.objects.get(number="1b1")).exists()
        is True
    )
    # Test has matched "//Not applicable"
    assert (
        other_options_qs.filter(question=Question.objects.get(number="6")).exists()
        is True
    )

    # Test that rows are preserved and duplicates are not generated
    import_command()
    results_qs = Result.objects.all()
    assert results_qs.count() == 6
    assert results_qs[0].num_options == 39
    assert results_qs[5].num_options == 64

    assert Question.objects.count() == 17
    assert QuestionCondition.objects.all().count() == 9

    assert question4.id == Question.objects.get(number="4").id
    new_joukkoliikenne = SubQuestion.objects.get(question=question4, order_number=2)
    assert joukkoliikenne.id == new_joukkoliikenne.id
    new_option_saa = Option.objects.get(sub_question=new_joukkoliikenne, order_number=3)
    new_option_saa_results = new_option_saa.results.all()
    assert new_option_saa_results.count() == 3
    assert option_saa_results[0].id == new_option_saa_results[0].id
    assert option_saa_results[1].id == new_option_saa_results[1].id
    assert option_saa_results[2].id == new_option_saa_results[2].id
    assert question8.id == Question.objects.get(number="8").id
    assert autoilija.id == Result.objects.get(topic_fi="Autoilija").id

    # Test that rows with info of Category 2 is skipped
    question8 = Question.objects.get(number="8")
    assert Option.objects.filter(question=question8).count() == 5
    condition = QuestionCondition.objects.get(question=question8)
    assert condition.question_condition == Question.objects.get(number="7")
    assert condition.option_conditions.all()[0].value_fi == "Ei."
