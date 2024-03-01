from django import forms
from django.contrib import admin

from .models import MailingList, Profile, User
from profiles.admin import DisableAddAdminMixin, DisableDeleteAdminMixin

admin.site.register(User)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "result")

    def result(self, obj):
        if obj.user.result:
            return obj.user.result.value
        else:
            return None


class MailingListAdminForm(forms.ModelForm):
    csv_emails = forms.CharField(widget=forms.Textarea(attrs={"rows": 20, "cols": 120}))

    class Meta:
        model = MailingList
        fields = ["result"]


class MailingListAdmin(DisableDeleteAdminMixin, DisableAddAdminMixin, admin.ModelAdmin):
    list_display = ("result", "csv_emails")

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


admin.site.register(Profile, ProfileAdmin)
admin.site.register(MailingList, MailingListAdmin)
