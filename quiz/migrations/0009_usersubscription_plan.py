# Generated by Django 5.0.6 on 2024-08-23 02:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0008_usersubscription"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersubscription",
            name="plan",
            field=models.CharField(default=1, max_length=200),
            preserve_default=False,
        ),
    ]