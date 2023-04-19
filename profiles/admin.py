from django.contrib import admin

from profiles.models import (
    Animal,
    Answer,
    Option,
    OptionGroup,
    Question,
    QuestionCondition,
    User,
)

admin.site.register(Question)
admin.site.register(QuestionCondition)
admin.site.register(Option)
admin.site.register(OptionGroup)
admin.site.register(Animal)
admin.site.register(Answer)
admin.site.register(User)
