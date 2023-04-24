from django.db import models


class QuestionCondition(models.Model):
    pass


class Question(models.Model):
    question = models.CharField(max_length=255, null=True)
    description = models.CharField(max_length=255, null=True)
    question_condition = models.OneToOneField(
        "QuestionCondition",
        related_name="question",
        null=True,
        on_delete=models.CASCADE,
    )


class OptionGroup(models.Model):
    description = models.CharField(max_length=255, null=True)
    additional_description = models.CharField(max_length=255, null=True)
    question = models.ForeignKey(
        "Question", related_name="option_groups", null=True, on_delete=models.CASCADE
    )


class Option(models.Model):
    value = models.CharField(max_length=255, null=True)
    affect_result = models.BooleanField(default=True)
    question = models.ForeignKey(
        "Question", related_name="options", on_delete=models.CASCADE, null=True
    )
    option_groups = models.ForeignKey(
        "OptionGroup", related_name="options", on_delete=models.CASCADE, null=True
    )
    results = models.ManyToManyField("Result", related_name="options")
    question_condition = models.ForeignKey(
        "QuestionCondition", related_name="options", on_delete=models.CASCADE, null=True
    )


class Result(models.Model):
    value = models.CharField(max_length=64, null=True)
    description = models.TextField(null=True)


class Answer(models.Model):
    user = models.ForeignKey("User", related_name="answers", on_delete=models.CASCADE)
    option = models.ForeignKey(
        "Option", related_name="answers", on_delete=models.CASCADE
    )


class User(models.Model):
    GENDER_OPTIONS = [
        ("M", "Male"),
        ("F", "Female"),
        ("NB", "Nonbinary"),
    ]
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True)
    result = models.ForeignKey(
        "Result", related_name="users", null=True, on_delete=models.CASCADE
    )
    email = models.EmailField(unique=True)
    gender = models.CharField(max_length=2, choices=GENDER_OPTIONS, blank=True)
