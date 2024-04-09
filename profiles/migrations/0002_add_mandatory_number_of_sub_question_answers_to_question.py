# Generated by Django 4.1.10 on 2023-09-21 09:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="question",
            name="number_of_sub_question_choices",
        ),
        migrations.AddField(
            model_name="question",
            name="mandatory_number_of_sub_questions_to_answer",
            field=models.CharField(default="*", max_length=2),
        ),
    ]
