# Generated by Django 5.0.6 on 2024-09-20 08:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0011_studytopicmodel_plan"),
    ]

    operations = [
        migrations.AddField(
            model_name="studycategorymodel",
            name="plan_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="study_categories",
                to="quiz.category",
            ),
        ),
        migrations.AlterField(
            model_name="studytopicmodel",
            name="plan",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="study_topics",
                to="quiz.category",
            ),
        ),
    ]
