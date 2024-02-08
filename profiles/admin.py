from django.contrib import admin

from profiles.models import (
    Answer,
    AnswerOther,
    Option,
    PostalCode,
    PostalCodeResult,
    PostalCodeType,
    Question,
    QuestionCondition,
    Result,
    SubQuestion,
    SubQuestionCondition,
)


class ReadOnlyFieldsAdminMixin:
    def has_change_permission(self, request, obj=None):
        return False


class DisableDeleteAdminMixin:
    def has_delete_permission(self, request, obj=None):
        return False


class QuestionAdmin(DisableDeleteAdminMixin, admin.ModelAdmin):
    class Meta:
        model = Question


class QuestionConditionAdmin(
    DisableDeleteAdminMixin, ReadOnlyFieldsAdminMixin, admin.ModelAdmin
):
    class Meta:
        model = QuestionCondition


class SubQuestionAdmin(DisableDeleteAdminMixin, admin.ModelAdmin):
    class Meta:
        model = Question


class ResultAdmin(DisableDeleteAdminMixin, admin.ModelAdmin):
    class Meta:
        model = Result


class SubQuestionConditionAdmin(
    DisableDeleteAdminMixin, ReadOnlyFieldsAdminMixin, admin.ModelAdmin
):
    class Meta:
        model = SubQuestionCondition


class OptionAdmin(DisableDeleteAdminMixin, ReadOnlyFieldsAdminMixin, admin.ModelAdmin):
    class Meta:
        model = Option


@admin.register(Answer)
class AnswerAdmin(DisableDeleteAdminMixin, ReadOnlyFieldsAdminMixin, admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(option__is_other=False)
        return qs

    class Meta:
        model = Answer


@admin.register(AnswerOther)
class AnswerOtherAdmin(
    DisableDeleteAdminMixin, ReadOnlyFieldsAdminMixin, admin.ModelAdmin
):
    list_display = (
        "question_description",
        "sub_question_description",
        "other",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(option__is_other=True)
        return qs

    def other(self, obj):
        return obj.option.other

    def question_description(self, obj):
        if obj.question:
            return obj.question.question_en
        else:
            return obj.sub_question.question.question_en

    def sub_question_description(self, obj):
        if obj.sub_question:
            return obj.sub_question.description_en
        return None

    class Meta:
        model = Answer


class PostalCodeAdmin(
    DisableDeleteAdminMixin, ReadOnlyFieldsAdminMixin, admin.ModelAdmin
):
    class Meta:
        model = PostalCode


class PostalCodeTypeAdmin(
    DisableDeleteAdminMixin, ReadOnlyFieldsAdminMixin, admin.ModelAdmin
):
    class Meta:
        model = PostalCodeType


class PostalCodeResultAdmin(
    DisableDeleteAdminMixin, ReadOnlyFieldsAdminMixin, admin.ModelAdmin
):
    class Meta:
        model = PostalCodeResult


admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionCondition, QuestionConditionAdmin)
admin.site.register(SubQuestion, SubQuestionAdmin)
admin.site.register(SubQuestionCondition, SubQuestionConditionAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(PostalCode, PostalCodeAdmin)
admin.site.register(PostalCodeType, PostalCodeTypeAdmin)
admin.site.register(PostalCodeResult, PostalCodeResultAdmin)
