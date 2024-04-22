import csv

from django.contrib import admin
from django.http import HttpResponse

from profiles.models import (
    Answer,
    AnswerOther,
    CumulativeResultCount,
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


class DisableAddAdminMixin:
    def has_add_permission(self, request, obj=None):
        return False


class DisableChangeAdminMixin:
    def has_change_permission(self, request, obj=None):
        return False


class DisableDeleteAdminMixin:
    def has_delete_permission(self, request, obj=None):
        return False


class QuestionAdmin(DisableDeleteAdminMixin, DisableAddAdminMixin, admin.ModelAdmin):
    class Meta:
        model = Question


class QuestionConditionAdmin(
    DisableDeleteAdminMixin,
    DisableChangeAdminMixin,
    DisableAddAdminMixin,
    admin.ModelAdmin,
):
    class Meta:
        model = QuestionCondition


class SubQuestionAdmin(DisableDeleteAdminMixin, DisableAddAdminMixin, admin.ModelAdmin):
    class Meta:
        model = Question


class ResultAdmin(
    DisableDeleteAdminMixin,
    DisableAddAdminMixin,
    DisableChangeAdminMixin,
    admin.ModelAdmin,
):
    class Meta:
        model = Result


class SubQuestionConditionAdmin(
    DisableDeleteAdminMixin,
    DisableChangeAdminMixin,
    DisableAddAdminMixin,
    admin.ModelAdmin,
):
    class Meta:
        model = SubQuestionCondition


class OptionAdmin(
    DisableDeleteAdminMixin,
    DisableChangeAdminMixin,
    DisableAddAdminMixin,
    admin.ModelAdmin,
):
    class Meta:
        model = Option


@admin.register(Answer)
class AnswerAdmin(
    DisableDeleteAdminMixin,
    DisableChangeAdminMixin,
    DisableAddAdminMixin,
    admin.ModelAdmin,
):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(option__is_other=False)
        return qs

    class Meta:
        model = Answer


@admin.register(AnswerOther)
class AnswerOtherAdmin(
    DisableDeleteAdminMixin,
    DisableChangeAdminMixin,
    DisableAddAdminMixin,
    admin.ModelAdmin,
):
    ordering = ["question", "sub_question"]

    actions = ["export_as_csv"]
    list_per_page = 10000
    list_display = (
        "question_number",
        "question_description",
        "sub_question_description",
        "other",
    )

    def question_number(self, obj):
        if obj.sub_question:
            return obj.sub_question.question.number
        return obj.question.number

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        queryset = queryset.order_by("question", "sub_question")
        field_names = ["id", "created", "question", "sub_question", "option", "other"]
        str_fields = ["question", "sub_question", "other"]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename={}.csv".format(meta)
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            row = []
            for field in field_names:
                attr = getattr(obj, field)
                if field == "question" and attr is None:
                    attr = obj.sub_question.question
                if field in str_fields:
                    attr = (
                        str(attr).replace('"', "'").replace("\n", " ").replace("\r", "")
                    )
                row.append(attr)
            writer.writerow(row)

        return response

    export_as_csv.short_description = "Export selected as CSV"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(option__is_other=True)

    def other(self, obj):
        return obj.option.other

    def question_description(self, obj):
        if obj.question:
            return obj.question.question_fi
        else:
            return obj.sub_question.question.question_fi

    def sub_question_description(self, obj):
        if obj.sub_question:
            return obj.sub_question.description_fi
        return None

    class Meta:
        model = Answer


class PostalCodeAdmin(
    DisableDeleteAdminMixin,
    DisableChangeAdminMixin,
    DisableAddAdminMixin,
    admin.ModelAdmin,
):
    class Meta:
        model = PostalCode


class PostalCodeTypeAdmin(
    DisableDeleteAdminMixin,
    DisableChangeAdminMixin,
    DisableAddAdminMixin,
    admin.ModelAdmin,
):
    class Meta:
        model = PostalCodeType


class PostalCodeResultAdmin(
    DisableDeleteAdminMixin,
    DisableChangeAdminMixin,
    DisableAddAdminMixin,
    admin.ModelAdmin,
):
    list_display = ("postal_code", "postal_code_type", "result", "count")

    class Meta:
        model = PostalCodeResult


@admin.register(CumulativeResultCount)
class CumulativeResultCountAdmin(
    DisableDeleteAdminMixin,
    DisableChangeAdminMixin,
    DisableAddAdminMixin,
    admin.ModelAdmin,
):
    # Admin view that displays the sum of the counts for Home or Optional postal code results for every result (animal).

    def changelist_view(self, request, extra_context=None):
        # Choose all rows, when selecting action.
        try:
            action = self.get_actions(request)[request.POST["action"]][0]
            action_acts_on_all = action.acts_on_all
        except (KeyError, AttributeError):
            action_acts_on_all = False
        if action_acts_on_all:
            post = request.POST.copy()
            post.setlist(
                admin.helpers.ACTION_CHECKBOX_NAME,
                self.model.objects.values_list("id", flat=True),
            )
            request.POST = post

        return admin.ModelAdmin.changelist_view(self, request, extra_context)

    list_display = ("value", "topic", "sum_of_count", "selected_postal_code_type")
    actions = ["home_postal_code_type", "optional_postal_code_type"]
    postal_code_type_name = PostalCodeType.HOME_POSTAL_CODE

    def home_postal_code_type(self, request, queryset):
        self.postal_code_type_name = PostalCodeType.HOME_POSTAL_CODE

    home_postal_code_type.acts_on_all = True

    def optional_postal_code_type(self, request, queryset):
        self.postal_code_type_name = PostalCodeType.OPTIONAL_POSTAL_CODE

    optional_postal_code_type.acts_on_all = True

    def selected_postal_code_type(self, obj):
        return self.postal_code_type_name

    def sum_of_count(self, obj):
        return obj.get_sum_of_count(self.postal_code_type_name)

    class Meta:
        model = CumulativeResultCount


admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionCondition, QuestionConditionAdmin)
admin.site.register(SubQuestion, SubQuestionAdmin)
admin.site.register(SubQuestionCondition, SubQuestionConditionAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(PostalCode, PostalCodeAdmin)
admin.site.register(PostalCodeType, PostalCodeTypeAdmin)
admin.site.register(PostalCodeResult, PostalCodeResultAdmin)
