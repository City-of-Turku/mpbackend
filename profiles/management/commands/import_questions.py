import logging
from typing import Any

import pandas as pd
from django.conf import settings
from django.core.management import BaseCommand

from profiles.models import Option, Question, Result, SubQuestion

logger = logging.getLogger(__name__)
FILENAME = "questions.xlsx"
IS_ANIMAL = 1

LANGUAGES = [language[0] for language in settings.LANGUAGES]
LANGUAGE_SEPARATOR = "/"
QUESTION_NUMBER_COLUMN = 0
QUESTION_COLUMN = 1
NUMBER_OF_CHOICES_COLUMN = 2
QUESTION_DESCRIPTION_COLUMN = 4
SUB_QUESTION_COLUMN = 5
SUB_QUESTION_DESCRIPTION_COLUMN = 7
OPTION_COLUMN = 8
RESULT_COLUMNS = [9, 10, 11, 12, 13, 14]


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
            except AttributeError:
                breakpoint()
        else:
            d[lang] = None
    return d


def get_and_create_results(data: pd.DataFrame) -> list:
    # Result.objects.all().delete()
    results_to_delete = list(Result.objects.all().values_list("id", flat=True))
    num_created = 0
    columns = data.columns[9:15]
    results = []
    for i, column in enumerate(columns):
        col_data = data[column]
        topic = get_language_dict(data.columns[9 + i])
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


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Question.objects.all().delete()
        file_path = f"{get_root_dir()}/media/{FILENAME}"
        excel_data = pd.read_excel(file_path, sheet_name="Yhdistetty")
        excel_data = excel_data.fillna("").replace([""], [None])
        results = get_and_create_results(excel_data)
        question = None
        sub_question = None
        sub_question_order_number = None
        option_order_number = None
        num_created = 0
        questions_to_delete = list(Question.objects.all().values_list("id", flat=True))
        for index, row_data in excel_data.iterrows():
            if index > 216:
                break
            try:
                question_number = str(row_data[QUESTION_NUMBER_COLUMN])
            except TypeError:
                continue
            if question_number[0].isdigit():
                questions = get_language_dict(row_data[QUESTION_COLUMN])
                descriptions = get_language_dict(row_data[QUESTION_DESCRIPTION_COLUMN])
                number_of_choices = row_data[NUMBER_OF_CHOICES_COLUMN]
                if not number_of_choices:
                    number_of_choices = 1
                filter = {
                    "number": question_number,
                    "number_of_choices": str(number_of_choices),
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
                save_translated_field(
                    sub_question, "description", get_language_dict(q_str)
                )
                desc_str = row_data[SUB_QUESTION_DESCRIPTION_COLUMN]
                if desc_str:
                    save_translated_field(
                        sub_question,
                        "additional_description",
                        get_language_dict(desc_str),
                    )

            # Create option
            if question or sub_question and row_data[OPTION_COLUMN]:
                if sub_question:
                    option, _ = Option.objects.get_or_create(
                        sub_question=sub_question, order_number=option_order_number
                    )
                else:
                    option, _ = Option.objects.get_or_create(
                        question=question, order_number=option_order_number
                    )
                option_order_number += 1
                val_str = row_data[OPTION_COLUMN]
                save_translated_field(option, "value", get_language_dict(val_str))
                for a_i, a_c in enumerate(RESULT_COLUMNS):
                    if row_data[a_c] == IS_ANIMAL:
                        option.results.add(results[a_i])
        Question.objects.filter(id__in=questions_to_delete).delete()
        logger.info(f"Created {num_created} questions")
