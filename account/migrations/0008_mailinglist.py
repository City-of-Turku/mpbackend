# Generated by Django 4.1.10 on 2024-01-12 08:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0009_subquestioncondition"),
        ("account", "0007_profile_age"),
    ]

    operations = [
        migrations.CreateModel(
            name="MailingList",
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
                    "result",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="mailing_list",
                        to="profiles.result",
                    ),
                ),
            ],
        ),
    ]
