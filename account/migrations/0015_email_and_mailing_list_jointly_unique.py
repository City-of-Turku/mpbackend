# Generated by Django 4.1.13 on 2024-04-30 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0014_remove_profile_is_filled_for_fun"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mailinglistemail",
            name="email",
            field=models.EmailField(max_length=254),
        ),
        migrations.AddConstraint(
            model_name="mailinglistemail",
            constraint=models.UniqueConstraint(
                fields=("email", "mailing_list"),
                name="email_and_mailing_list_must_be_jointly:unique",
            ),
        ),
    ]
