from modeltranslation.translator import TranslationOptions, translator

from profiles.models import Option, Question, Result, SubQuestion


class QuestionTranslationOptions(TranslationOptions):
    fields = (
        "question",
        "description",
    )


translator.register(Question, QuestionTranslationOptions)


class SubQuestionTranslationOptions(TranslationOptions):
    fields = (
        "description",
        "additional_description",
    )


translator.register(SubQuestion, SubQuestionTranslationOptions)


class OptionTranslationOptions(TranslationOptions):
    fields = ("value",)


translator.register(Option, OptionTranslationOptions)


class ResultTranslationOptions(TranslationOptions):
    fields = ("topic", "value", "description")


translator.register(Result, ResultTranslationOptions)
