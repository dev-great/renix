# Generated by Django 5.0.6 on 2024-09-24 02:32

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0012_studycategorymodel_plan_group_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='READINESSASSESSMENT',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('topic', models.CharField(choices=[('Management of Care', 'Management of Care'), ('Safety and Infection Control', 'Safety and Infection Control'), ('Health Promotion and Maintenance', 'Health Promotion and Maintenance'), ('Psychosocial Integrity', 'Psychosocial Integrity'), ('Basic Care and Comfort', 'Basic Care and Comfort'), ('Pharmacological and Parenteral Therapies', 'Pharmacological and Parenteral Therapies'), ('Reduction of Risk Potential', 'Reduction of Risk Potential'), ('Physiological Adaptation', 'Physiological Adaptation'), ('Adult Health', 'Adult Health'), ('Child Health', 'Child Health'), ('Critical Care', 'Critical Care'), ('Fundamentals', 'Fundamentals'), ('Leadership & Management', 'Leadership & Management'), ('Maternal & Newborn Health', 'Maternal & Newborn Health'), ('Mental Health', 'Mental Health'), ('Pharmacology', 'Pharmacology'), ('Postpartum', 'Postpartum'), ('Prioritization', 'Prioritization'), ('Newborn', 'Newborn'), ('Assignment/Delegation', 'Assignment/Delegation')], max_length=100)),
                ('question', models.TextField()),
                ('mark', models.IntegerField(default=5)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rediness_questions', to='quiz.studytopicmodel')),
            ],
            options={
                'ordering': ['uid'],
            },
        ),
    ]