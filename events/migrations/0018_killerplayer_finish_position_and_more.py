# Generated by Django 4.2.21 on 2025-06-06 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0017_remove_killerconfig_lives_per_player'),
    ]

    operations = [
        migrations.AddField(
            model_name='killerplayer',
            name='finish_position',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='killerplayer',
            name='points_awarded',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
