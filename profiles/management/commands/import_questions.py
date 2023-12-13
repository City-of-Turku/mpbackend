import logging
from typing import Any

import pandas as pd
from django import db
from django.conf import settings
from django.core.management import BaseCommand

from profiles.models import (
    Option,
    Question,
    QuestionCondition,
    Result,
    SubQuestion,
    SubQuestionCondition,
)

logger = logging.getLogger(__name__)
FILENAME = "questions.xlsx"
IS_ANIMAL = 1

LANGUAGES = [language[0] for language in settings.LANGUAGES]
LANGUAGE_SEPARATOR = "/"
QUESTION_NUMBER_COLUMN = 0
QUESTION_COLUMN = 1
NUMBER_OF_OPTIONS_TO_CHOOSE = 2
CONDITION_COLUMN = 3
QUESTION_DESCRIPTION_COLUMN = 4
SUB_QUESTION_COLUMN = 5
MANDATORY_NUMBER_OF_SUB_QUESTIONS_TO_ANSWER_COLUMN = 6
SUB_QUESTION_DESCRIPTION_COLUMN = 7
SUB_QUESTION_CONDITION_COLUMN = 8

OPTION_COLUMN = 9
RESULT_COLUMNS = [10, 11, 12, 13, 14, 15]


def get_root_dir() -> str:
    """
    Returns the root directory of the project.
    """
    if hasattr(settings, "PROJECT_ROOT"):
        return settings.PROJECT_ROOT
    else:
        return settings.BASE_DIR


def save_translated_field(obj: Any, field_name: str, data: dict):
    """
    Sets the value of all languages for given field_name.
    :param obj: the object to which the fields will be set
    :param field_name:  name of the field to be set.
    :param data: dictionary where the key is the language and the value is the value
    to be set for the field with the given langauge.
    """
    for lang in LANGUAGES:
        if lang in data:
            obj_key = "{}_{}".format(field_name, lang)
            setattr(obj, obj_key, data[lang])
    obj.save()


def get_language_dict(data: str) -> dict:
    data = str(data).split(LANGUAGE_SEPARATOR)
    d = {}
    for i, lang in enumerate(LANGUAGES):
        if i < len(data):
            try:
                d[lang] = data[i].strip()
            except AttributeError as e:
                logger.error(f"AttributeError {e}")
        else:
            d[lang] = None
    return d


@db.transaction.atomic
def get_and_create_results(data: pd.DataFrame) -> list:
    results_to_delete = list(Result.objects.all().values_list("id", flat=True))
    num_created = 0

    columns = data.columns[RESULT_COLUMNS[0] : RESULT_COLUMNS[-1] + 1]
    results = []
    for i, column in enumerate(columns):
        col_data = data[column]
        topic = get_language_dict(data.columns[RESULT_COLUMNS[0] + i])
        value = get_language_dict(col_data[1])
        description = get_language_dict(col_data[0])
        filter = {}
        for lang in LANGUAGES:
            filter[f"topic_{lang}"] = topic[lang]
            filter[f"value_{lang}"] = value[lang]
            filter[f"description_{lang}"] = description[lang]
        queryset = Result.objects.filter(**filter)
        if queryset.count() == 0:
            result = Result.objects.create(**filter)
            logger.info(f"Created Result: {topic['fi']}")
            num_created += 1
        else:
            result = queryset.first()
            id = queryset.first().id
            if id in results_to_delete:
                results_to_delete.remove(id)

        results.append(result)
    Result.objects.filter(id__in=results_to_delete).delete()
    logger.info(f"Created {num_created} Results")
    return results


@db.transaction.atomic
def create_sub_question_condition(row_data: str, sub_question: SubQuestion):
    question_number, option_order_number = row_data.split(".")
    question = Question.objects.get(number=question_number)
    option = Option.objects.get(question=question, order_number=option_order_number)
    SubQuestionCondition.objects.create(sub_question=sub_question, option=option)


@db.transaction.atomic
def create_conditions(row_data: str, question: Question):
    # Hack as e.g. "7,1" in excel cell is interpreted as float even though it is formated to str in excel.
    if type(row_data) != str:
        row_data = str(row_data).replace(".", ",")
    question_separator = ":"
    option_separator = ","
    question_sub_question_separator = "."
    conditions = row_data.split(question_separator)
    for cond in conditions:
        if option_separator in cond:
            question_subquestion, options = cond.split(option_separator)
            options = options.split("-")
        else:
            question_subquestion = cond
            options = []
        tmp = question_subquestion.split(question_sub_question_separator)
        question_number = tmp[0]
        question_condition = Question.objects.get(number=question_number)
        sub_question_condition = None
        if len(tmp) == 2:
            sub_question_order_number = tmp[1]
            sub_question_condition = SubQuestion.objects.get(
                question=question_condition, order_number=sub_question_order_number
            )
            options_qs = Option.objects.filter(
                sub_question=sub_question_condition, order_number__in=options
            )
        else:
            options_qs = Option.objects.filter(
                question=question_condition, order_number__in=options
            )

        question_condition, created = QuestionCondition.objects.get_or_create(
            question=question,
            question_condition=question_condition,
            sub_question_condition=sub_question_condition,
        )
        if created:
            question_condition.option_conditions.add(*options_qs)


@db.transaction.atomic
def save_questions(excel_data: pd.DataFrame, results: list):
    question = None
    sub_question = None
    sub_question_order_number = None
    option_order_number = None
    num_created = 0
    questions_to_delete = list(Question.objects.all().values_list("id", flat=True))
    for index, row_data in excel_data.iterrows():
        # The end of the questions sheet includes questions that will not be imported.
        if index > 214:
            break
        try:
            question_number = str(row_data[QUESTION_NUMBER_COLUMN])
        except TypeError:
            continue

        if question_number[0].isdigit():
            questions = get_language_dict(row_data[QUESTION_COLUMN])
            descriptions = get_language_dict(row_data[QUESTION_DESCRIPTION_COLUMN])
            number_of_options_to_choose = row_data[NUMBER_OF_OPTIONS_TO_CHOOSE]
            if not number_of_options_to_choose:
                number_of_options_to_choose = "1"

            mandatory_number_of_sub_questions_to_answer = row_data[
                MANDATORY_NUMBER_OF_SUB_QUESTIONS_TO_ANSWER_COLUMN
            ]
            if not mandatory_number_of_sub_questions_to_answer:
                mandatory_number_of_sub_questions_to_answer = "*"
            filter = {
                "number": question_number,
                "number_of_options_to_choose": str(number_of_options_to_choose),
                "mandatory_number_of_sub_questions_to_answer": str(
                    mandatory_number_of_sub_questions_to_answer
                ).replace(".0", ""),
            }
            for lang in LANGUAGES:
                filter[f"question_{lang}"] = questions[lang]
                filter[f"description_{lang}"] = descriptions[lang]

            queryset = Question.objects.filter(**filter)
            if queryset.count() == 0:
                question = Question.objects.create(**filter)
                logger.info(f"Created question: {questions['fi']}")
                num_created += 1
            else:

                logger.info(f"Found question: {questions['fi']}")
                question = queryset.first()
                id = queryset.first().id
                if id in questions_to_delete:
                    questions_to_delete.remove(id)
            if row_data[CONDITION_COLUMN]:
                create_conditions(row_data[CONDITION_COLUMN], question)
            sub_question_order_number = 0
            option_order_number = 0
            sub_question = None

        # Create SubQuestion
        if question and row_data[SUB_QUESTION_COLUMN]:
            logger.info(f"created sub question {row_data[SUB_QUESTION_COLUMN]}")
            sub_question, _ = SubQuestion.objects.get_or_create(
                question=question, order_number=sub_question_order_number
            )
            sub_question_order_number += 1
            option_order_number = 0
            q_str = row_data[SUB_QUESTION_COLUMN]
            save_translated_field(sub_question, "description", get_language_dict(q_str))
            desc_str = row_data[SUB_QUESTION_DESCRIPTION_COLUMN]
            if desc_str:
                save_translated_field(
                    sub_question,
                    "additional_description",
                    get_language_dict(desc_str),
                )
            if row_data[SUB_QUESTION_CONDITION_COLUMN]:
                create_sub_question_condition(
                    row_data[SUB_QUESTION_CONDITION_COLUMN], sub_question
                )

        # Create option
        if question or sub_question and row_data[OPTION_COLUMN]:
            val_str = row_data[OPTION_COLUMN]
            if sub_question:
                option, _ = Option.objects.get_or_create(
                    sub_question=sub_question, order_number=option_order_number
                )
            else:
                # Skips rows with category info
                if not val_str:
                    continue
                option, _ = Option.objects.get_or_create(
                    question=question, order_number=option_order_number
                )

            option_order_number += 1
            save_translated_field(option, "value", get_language_dict(val_str))
            for a_i, a_c in enumerate(RESULT_COLUMNS):
                if row_data[a_c] == IS_ANIMAL:
                    option.results.add(results[a_i])
    Question.objects.filter(id__in=questions_to_delete).delete()
    logger.info(f"Created {num_created} questions")


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Question.objects.all().delete()
        # QuestionCondition.objects.all().delete()
        # Result.objects.all().delete()

        file_path = f"{get_root_dir()}/media/{FILENAME}"
        excel_data = pd.read_excel(file_path, sheet_name="Yhdistetty")
        excel_data = excel_data.fillna("").replace([""], [None])
        results = get_and_create_results(excel_data)
        save_questions(excel_data, results)
