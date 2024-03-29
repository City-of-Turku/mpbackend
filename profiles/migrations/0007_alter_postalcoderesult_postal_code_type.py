# Generated by Django 4.1.10 on 2023-09-29 07:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0006_add_model_postalcodetype"),
    ]

    operations = [
        migrations.AlterField(
            model_name="postalcoderesult",
            name="postal_code_type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="postal_code_results",
                to="profiles.postalcodetype",
            ),
        ),
    ]
