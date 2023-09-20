from django.db import models


class Question(models.Model):
    number = models.CharField(max_length=3, null=True)
    question = models.CharField(max_length=255, null=True)
    description = models.CharField(max_length=255, null=True)
    number_of_choices = models.CharField(max_length=2, default="1")

    number_of_sub_question_choices = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"question number:{self.number}, question: {self.question}"


class SubQuestion(models.Model):
    description = models.CharField(max_length=255, null=True)
    additional_description = models.CharField(max_length=255, null=True)
    question = models.ForeignKey(
        "Question", related_name="sub_questions", null=True, on_delete=models.CASCADE
    )
    order_number = models.PositiveSmallIntegerField(null=True)

    class Meta:
        ordering = ["question__number"]

    def __str__(self):
        return f"{self.description}"


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
    order_number = models.PositiveSmallIntegerField(null=True)

    class Meta:
        ordering = ["question__number", "sub_question__question__number"]

    def __str__(self):
        return f"Value: {self.value}"


class Result(models.Model):
    topic = models.CharField(max_length=64, null=True)
    value = models.CharField(max_length=64, null=True)
    description = models.TextField(null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.topic} / {self.value}"


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
        ordering = ["id"]


class QuestionCondition(models.Model):
    question = models.ForeignKey(
        "Question",
        related_name="conditions",
        null=True,
        on_delete=models.CASCADE,
    )

    question_condition = models.ForeignKey(
        "Question",
        related_name="question_conditions",
        null=True,
        on_delete=models.CASCADE,
    )
    sub_question_condition = models.ForeignKey(
        "SubQuestion",
        related_name="sub_question_conditions",
        null=True,
        on_delete=models.CASCADE,
    )
    option_conditions = models.ManyToManyField(
        "Option", related_name="option_conditions"
    )
