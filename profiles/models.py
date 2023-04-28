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
    number_of_choices = models.PositiveSmallIntegerField(default=1)
    number_of_sub_question_choices = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["pk"]


class SubQuestion(models.Model):
    description = models.CharField(max_length=255, null=True)
    additional_description = models.CharField(max_length=255, null=True)
    question = models.ForeignKey(
        "Question", related_name="sub_questions", null=True, on_delete=models.CASCADE
    )


class Option(models.Model):
    value = models.CharField(max_length=255, null=True)
    affect_result = models.BooleanField(default=True)
    question = models.ForeignKey(
        "Question", related_name="options", on_delete=models.CASCADE, null=True
    )
    sub_question = models.ForeignKey(
        "SubQuestion", related_name="options", on_delete=models.CASCADE, null=True
    )
    results = models.ManyToManyField("Result", related_name="options")
    question_condition = models.ForeignKey(
        "QuestionCondition", related_name="options", on_delete=models.CASCADE, null=True
    )


class Result(models.Model):
    value = models.CharField(max_length=64, null=True)
    description = models.TextField(null=True)


class Answer(models.Model):
    user = models.ForeignKey(
        "account.User", related_name="answers", on_delete=models.CASCADE
    )
    option = models.ForeignKey(
        "Option", related_name="answers", on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "option"], name="unique_user_and_option"
            )
        ]
