import re

import pandas as pd
from django.conf import settings
from django.core.management import BaseCommand

from profiles.models import Option, Question, Result, SubQuestion


FILENAME = "prof2.xlsx"
IS_ANIMAL = 1

LANGUAGES = [language[0] for language in settings.LANGUAGES]
LANGUAGE_SEPARATOR = "/"
QUESTION_COLUMN = 1
QUESTION_DESCRIPTION_COLUMN = 4
SUB_QUESTION_COLUMN = 5
SUB_QUESTION_DESCRIPTION_COLUMN = 7

OPTION_COLUMN = 8


def get_root_dir():
    """
    Returns the root directory of the project.
    """
    if hasattr(settings, "PROJECT_ROOT"):
        return settings.PROJECT_ROOT
    else:
        return settings.BASE_DIR


def get_or_create_results(data):
    Result.objects.all().delete()
    columns = data.columns[9:15]
    results = []
    for column in columns:
        col_data = data[column]
        result, _ = Result.objects.get_or_create(
            value=col_data[1], description=col_data[0]
        )
        results.append(result)
    return results


def save_translated_field(obj, field_name, data):
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


def get_language_dict(data):
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


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Index number of columns containin results to options
        result_columns = [9, 10, 11, 12, 13, 14]
        file_path = f"{get_root_dir()}/media/{FILENAME}"
        excel_data = pd.read_excel(file_path, sheet_name="FIN")
        # excel_data = excel_data.fillna(None)
        excel_data = excel_data.fillna("").replace([""], [None])
        results = get_or_create_results(excel_data.iloc[0:3])
        Question.objects.all().delete()
        question = None
        sub_question = None
        num_rows = 0
        question_description_created = False
        for row in excel_data.iterrows():
            num_rows += 1

            # TODO, remove when excel file changes are complete
            if num_rows > 226:
                return

            row_data = row[1]
            try:
                col_0 = str(row_data[0])
            except TypeError:
                continue

            if col_0[0].isdigit():
                question = Question.objects.create()
                q_str = row_data[QUESTION_COLUMN]

                save_translated_field(question, "question", get_language_dict(q_str))
                desc_str = row_data[QUESTION_DESCRIPTION_COLUMN]
                if desc_str:
                    save_translated_field(
                        question, "description", get_language_dict(desc_str)
                    )

                sub_question = None

            # Create SubQuestion
            if question and row_data[SUB_QUESTION_COLUMN]:
                print(f"create sub question {row_data[SUB_QUESTION_COLUMN]}")
                sub_question = SubQuestion.objects.create(question=question)
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
                    option = Option.objects.create(sub_question=sub_question)
                else:
                    option = Option.objects.create(question=question)

                val_str = row_data[OPTION_COLUMN]
                save_translated_field(option, "value", get_language_dict(val_str))
                for a_i, a_c in enumerate(result_columns):
                    if row_data[a_c] == IS_ANIMAL:
                        option.results.add(results[a_i])
