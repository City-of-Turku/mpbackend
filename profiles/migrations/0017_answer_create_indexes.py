# Generated by Django 4.2 on 2024-02-29 08:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0016_result_value_result_value_en_result_value_fi_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="answer",
            index=models.Index(
                fields=["user", "question", "sub_question"],
                name="profiles_an_user_id_8141b8_idx",
            ),
        ),
    ]
