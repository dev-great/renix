# Generated by Django 5.0.6 on 2024-08-25 01:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0010_alter_studymodel_video_uri"),
    ]

    operations = [
        migrations.AddField(
            model_name="studytopicmodel",
            name="plan",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="plan",
                to="quiz.category",
            ),
            preserve_default=False,
        ),
    ]