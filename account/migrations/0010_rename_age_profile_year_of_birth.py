# Generated by Django 4.1.10 on 2024-01-17 12:16

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0009_mailinglistemail"),
    ]

    operations = [
        migrations.RenameField(
            model_name="profile",
            old_name="age",
            new_name="year_of_birth",
        ),
    ]
