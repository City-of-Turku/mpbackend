from django.contrib import admin

from profiles.models import (
    Answer,
    Option,
    Question,
    QuestionCondition,
    Result,
    SubQuestion,
    User,
)

admin.site.register(Question)
admin.site.register(QuestionCondition)
admin.site.register(Option)
admin.site.register(SubQuestion)
admin.site.register(Result)
admin.site.register(Answer)
admin.site.register(User)
