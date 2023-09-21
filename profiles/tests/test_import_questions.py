from io import StringIO

import pytest
from django.core.management import call_command

from profiles.models import Option, Question, QuestionCondition, Result, SubQuestion


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
    assert results_qs[1].value_sv == "Rutinerad Räv"
    assert results_qs[2].description_en[0:15] == "Travels by foot"
    assert results_qs[3].topic_en == "Public transport passenger"
    assert results_qs[4].value_fi == "Kokeileva Kauris"
    assert results_qs[5].description_sv[-12:] == "använda bil."

    # Test questions
    assert Question.objects.count() == 20
    # Test question without sub questions
    question1b1 = Question.objects.get(number="1b1")
    assert question1b1.question_fi == "Miksi et koskaan kulje autolla?"
    assert question1b1.number_of_choices == "*"
    # Test Sub questions
    question1 = Question.objects.get(number="1")
    assert question1.num_sub_questions == 8
    assert question1.number_of_choices == "1"
    assert question1.description_en[0:2] == "If"
    sub_q_qs = SubQuestion.objects.filter(question=question1)
    assert sub_q_qs.count() == 8
    sq_auto = sub_q_qs.get(order_number=0)
    assert sq_auto.description_en == "Car"
    assert Option.objects.filter(sub_question=sq_auto).count() == 6
    sq_auto_4_5 = Option.objects.get(sub_question=sq_auto, order_number=4)
    assert sq_auto_4_5.value == "4-5"
    sq_auto_4_5_results = sq_auto_4_5.results.all()
    assert sq_auto_4_5_results.count() == 2
    assert sq_auto_4_5_results[0] == autoilija
    assert sq_auto_4_5_results[1].topic_en == "Habit traveler"

    sq_walk = sub_q_qs.get(order_number=6)
    sq_walk.description_sv == "Gående"
    assert Option.objects.filter(sub_question=sq_walk).count() == 6
    assert Option.objects.get(sub_question=sq_walk, order_number=2).value == "1"
    question1d = Question.objects.get(number="1d")
    assert question1d.num_sub_questions == 0
    assert Option.objects.filter(question=question1d).count() == 3
    assert Option.objects.get(question=question1d, order_number=1).value == "Joskus"

    question4 = Question.objects.get(number="4")
    assert question4.mandatory_number_of_sub_questions_to_answer == "3"
    assert SubQuestion.objects.filter(question=question4).count() == 6
    joukkoliikenne = SubQuestion.objects.get(question=question4, order_number=2)
    assert (
        joukkoliikenne.additional_description
        == "Tärkein syy, miksi käytän joukkoliikennettä on:"
    )
    assert Option.objects.filter(sub_question=joukkoliikenne).count() == 12
    option_saa = Option.objects.get(sub_question=joukkoliikenne, order_number=3)
    assert option_saa.value == "säätila (sade, tuuli, jne.)"
    option_saa_results = option_saa.results.all()
    assert option_saa_results.count() == 3
    assert option_saa_results[0].topic_fi == "Joukkoliikenteen käyttäjä"
    assert option_saa_results[1].topic_sv == "MaaS-resenär"
    assert option_saa_results[2].topic_en == "Conscious traveler"
    question14 = Question.objects.get(number="14")
    assert question14.options.count() == 2
    assert question14.options.all()[1].value_en == "most comfortable route"
    # Test question condition
    assert QuestionCondition.objects.all().count() == 13
    conditions = QuestionCondition.objects.filter(question=question14)
    assert conditions.count() == 2
    sq_train = SubQuestion.objects.get(question=question1, order_number=2)
    condition = conditions.get(
        question_condition=question1, sub_question_condition=sq_train
    )
    assert condition.option_conditions.count() == 5
    assert condition.option_conditions.all()[0].value == "<1"
    assert condition.option_conditions.all()[4].value == "6-7"
    # Test that rows are preserved and duplicates are not generated
    import_command()
    assert Result.objects.count() == 6
    assert Question.objects.count() == 20
    assert QuestionCondition.objects.all().count() == 13

    assert question4.id == Question.objects.get(number="4").id
    new_joukkoliikenne = SubQuestion.objects.get(question=question4, order_number=2)
    assert joukkoliikenne.id == new_joukkoliikenne.id
    new_option_saa = Option.objects.get(sub_question=new_joukkoliikenne, order_number=3)
    new_option_saa_results = new_option_saa.results.all()
    assert new_option_saa_results.count() == 3
    assert option_saa_results[0].id == new_option_saa_results[0].id
    assert option_saa_results[1].id == new_option_saa_results[1].id
    assert option_saa_results[2].id == new_option_saa_results[2].id
    assert question14.id == Question.objects.get(number="14").id
    assert autoilija.id == Result.objects.get(topic_fi="Autoilija").id
    question8 = Question.objects.get(number="8")
    condition = QuestionCondition.objects.get(question=question8)
    assert condition.question_condition == Question.objects.get(number="7")
    assert condition.option_conditions.all()[0].value_fi == "Ei"
    question10 = Question.objects.get(number="10")
    assert question10.options.count() == 5
