from django.contrib import admin

from profiles.models import (
    Answer,
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


class AnswerAdmin(DisableDeleteAdminMixin, ReadOnlyFieldsAdminMixin, admin.ModelAdmin):
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
admin.site.register(Answer, AnswerAdmin)
admin.site.register(PostalCode, PostalCodeAdmin)
admin.site.register(PostalCodeType, PostalCodeTypeAdmin)
admin.site.register(PostalCodeResult, PostalCodeResultAdmin)
