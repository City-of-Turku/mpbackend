from modeltranslation.translator import TranslationOptions, translator

from profiles.models import Result, Option, OptionGroup, Question


class QuestionTranslationOptions(TranslationOptions):
    fields = (
        "question",
        "description",
    )


translator.register(Question, QuestionTranslationOptions)


class OptionGroupTranslationOptions(TranslationOptions):
    fields = (
        "description",
        "additional_description",
    )


translator.register(OptionGroup, OptionGroupTranslationOptions)


class OptionTranslationOptions(TranslationOptions):
    fields = ("value",)


translator.register(Option, OptionTranslationOptions)


class ResultTranslationOptions(TranslationOptions):
    fields = ("value", "description")


translator.register(Result, ResultTranslationOptions)
