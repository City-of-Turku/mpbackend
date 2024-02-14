from django.db import models


class Question(models.Model):
    number = models.CharField(max_length=3, null=True)
    question = models.CharField(max_length=255, null=True)
    description = models.CharField(max_length=255, null=True)
    number_of_options_to_choose = models.CharField(max_length=2, default="1")
    mandatory_number_of_sub_questions_to_answer = models.CharField(
        max_length=2, default="*"
    )

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"question number:{self.number}, question: {self.question}"

    @property
    def num_sub_questions(self):
        return self.sub_questions.count()


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
    is_other = models.BooleanField(default=False, verbose_name="is other textfield")

    class Meta:
        ordering = ["order_number"]

    def __str__(self):
        return f"Value: {self.value}"


class Result(models.Model):
    topic = models.CharField(max_length=64, null=True)
    description = models.TextField(null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.topic}"


class Answer(models.Model):
    user = models.ForeignKey(
        "account.User", related_name="answers", on_delete=models.CASCADE
    )
    option = models.ForeignKey(
        "Option", related_name="answers", null=True, on_delete=models.CASCADE
    )
    other = models.TextField(null=True, blank=True)

    question = models.ForeignKey(
        "Question", related_name="answers", null=True, on_delete=models.CASCADE
    )
    sub_question = models.ForeignKey(
        "SubQuestion", related_name="answers", null=True, on_delete=models.CASCADE
    )

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]


class AnswerOther(Answer):
    # Proxy model that allows registerin Answer model twice to the Admin
    class Meta:
        proxy = True


class QuestionCondition(models.Model):
    question = models.ForeignKey(
        "Question",
        related_name="question_conditions",
        null=True,
        on_delete=models.CASCADE,
    )

    question_condition = models.ForeignKey(
        "Question",
        related_name="condition_question_conditions",
        null=True,
        on_delete=models.CASCADE,
    )
    sub_question_condition = models.ForeignKey(
        "SubQuestion",
        related_name="question_conditions",
        null=True,
        on_delete=models.CASCADE,
    )
    option_conditions = models.ManyToManyField(
        "Option", related_name="question_conditions"
    )


class SubQuestionCondition(models.Model):
    sub_question = models.ForeignKey(
        "SubQuestion",
        related_name="sub_question_conditions",
        null=True,
        on_delete=models.CASCADE,
    )
    option = models.ForeignKey(
        "Option",
        null=True,
        on_delete=models.CASCADE,
        related_name="sub_question_conditions",
    )


class PostalCode(models.Model):
    postal_code = models.CharField(max_length=10, null=True)

    def __str__(self):
        return f"{self.postal_code}"


class PostalCodeType(models.Model):
    HOME_POSTAL_CODE = "Home"
    OPTIONAL_POSTAL_CODE = "Optional"
    POSTAL_CODE_TYPE_CHOICES = [
        (HOME_POSTAL_CODE, HOME_POSTAL_CODE),
        (OPTIONAL_POSTAL_CODE, OPTIONAL_POSTAL_CODE),
    ]
    type_name = models.CharField(
        max_length=8,
        null=True,
        choices=POSTAL_CODE_TYPE_CHOICES,
        default=OPTIONAL_POSTAL_CODE,
    )

    def __str__(self):
        return f"{self.type_name}"


class PostalCodeResult(models.Model):
    postal_code = models.ForeignKey(
        "PostalCode",
        null=True,
        on_delete=models.CASCADE,
        related_name="postal_code_results",
    )

    postal_code_type = models.ForeignKey(
        "PostalCodeType",
        null=True,
        on_delete=models.CASCADE,
        related_name="postal_code_results",
    )
    result = models.ForeignKey(
        "Result", related_name="postal_code_results", on_delete=models.CASCADE
    )
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    models.Q(postal_code__isnull=True)
                    & models.Q(postal_code_type__isnull=True)
                )
                | models.Q(
                    models.Q(postal_code__isnull=False)
                    & models.Q(postal_code_type__isnull=False)
                ),
                name="postal_code_and_postal_code_type_must_be_jointly_null",
            )
        ]

    def __str__(self):
        if self.postal_code and self.postal_code_type:
            return f"{self.postal_code_type} postal_code: {self.postal_code}, count: {self.count}"
        else:
            return f"count: {self.count}"
