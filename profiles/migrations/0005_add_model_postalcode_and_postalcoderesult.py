# Generated by Django 4.1.10 on 2023-09-27 05:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "profiles",
            "0004_rename_number_of_choices_question_number_of_options_to_choose",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="PostalCode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("postal_code", models.CharField(max_length=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="PostalCodeResult",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "postal_code_type",
                    models.CharField(
                        choices=[("Home", "Home"), ("Work", "Work")],
                        default="Work",
                        max_length=4,
                        null=True,
                    ),
                ),
                ("count", models.PositiveIntegerField(default=0)),
                (
                    "postal_code",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="postal_code_results",
                        to="profiles.postalcode",
                    ),
                ),
                (
                    "result",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="postal_code_results",
                        to="profiles.result",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="postalcoderesult",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("postal_code__isnull", True),
                        ("postal_code_type__isnull", True),
                    ),
                    models.Q(
                        ("postal_code__isnull", False),
                        ("postal_code_type__isnull", False),
                    ),
                    _connector="OR",
                ),
                name="postal_code_and_postal_code_type_must_be_jointly_null",
            ),
        ),
    ]
