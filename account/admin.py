from django import forms
from django.contrib import admin

from profiles.admin import DisableAddAdminMixin, DisableDeleteAdminMixin

from .models import MailingList, Profile, User


class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "date_joined")
    ordering = ["-date_joined"]


class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "result", "date_joined")

    ordering = ["-user__date_joined"]

    def result(self, obj):
        if obj.user.result:
            return obj.user.result.value
        else:
            return None

    def date_joined(self, obj):
        return obj.user.date_joined


class MailingListAdminForm(forms.ModelForm):
    csv_emails = forms.CharField(widget=forms.Textarea(attrs={"rows": 20, "cols": 120}))

    class Meta:
        model = MailingList
        fields = ["result"]


class MailingListAdmin(DisableDeleteAdminMixin, DisableAddAdminMixin, admin.ModelAdmin):
    list_display = ("result", "number_of_emails")

    readonly_fields = ("result",)
    form = MailingListAdminForm

    def csv_emails(self, obj):
        return obj.csv_emails

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["csv_emails"].initial = self.csv_emails(obj)
        return form

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_save_and_add_another"] = False
        extra_context["show_save_and_continue"] = False
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(MailingList, MailingListAdmin)
