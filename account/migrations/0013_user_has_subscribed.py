# Generated by Django 4.1.13 on 2024-04-10 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0012_profile_is_interested_in_mobility"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="has_subscribed",
            field=models.BooleanField(default=False),
        ),
    ]