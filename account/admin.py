from django.contrib import admin

from .models import Profile, User

admin.site.register(User)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "gender"]
