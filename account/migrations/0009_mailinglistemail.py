# Generated by Django 4.1.10 on 2024-01-12 09:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0008_mailinglist"),
    ]

    operations = [
        migrations.CreateModel(
            name="MailingListEmail",
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
                ("email", models.EmailField(max_length=254, unique=True)),
                (
                    "mailing_list",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="emails",
                        to="account.mailinglist",
                    ),
                ),
            ],
        ),
    ]
