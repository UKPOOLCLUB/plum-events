# Generated by Django 4.2.21 on 2025-06-20 03:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0027_edartsgroup_scorekeeper'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='edarts_completed',
        ),
        migrations.AddField(
            model_name='edartsgroup',
            name='submitted',
            field=models.BooleanField(default=False),
        ),
    ]
