# Generated by Django 4.1.10 on 2024-02-07 07:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0012_option_is_other"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnswerOther",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("profiles.answer",),
        ),
    ]