# Generated by Django 5.0.3 on 2024-03-06 07:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0011_profile_gender"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="is_interested_in_mobility",
            field=models.BooleanField(default=False),
        ),
    ]
