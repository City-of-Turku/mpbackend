# Generated by Django 4.1.13 on 2024-04-30 11:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0015_email_and_mailing_list_jointly_unique"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={"ordering": ["-date_joined"]},
        ),
    ]