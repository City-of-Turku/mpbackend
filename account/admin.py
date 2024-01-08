from django.contrib import admin

from .models import Profile, User

admin.site.register(User)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "result")

    def result(self, obj):
        if obj.user.result:
            return obj.user.result.value
        else:
            return None


admin.site.register(Profile, ProfileAdmin)
