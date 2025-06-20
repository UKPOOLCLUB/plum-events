# Generated by Django 4.2.21 on 2025-06-18 03:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0025_alter_minigolfconfig_holes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='minigolfconfig',
            name='overall_bonus',
        ),
        migrations.AddField(
            model_name='minigolfconfig',
            name='points_fifth',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='minigolfconfig',
            name='points_fourth',
            field=models.IntegerField(default=10),
        ),
        migrations.AlterField(
            model_name='minigolfconfig',
            name='points_second',
            field=models.IntegerField(default=35),
        ),
        migrations.AlterField(
            model_name='minigolfconfig',
            name='points_third',
            field=models.IntegerField(default=20),
        ),
        migrations.AlterField(
            model_name='poolleagueconfig',
            name='frames_per_match',
            field=models.IntegerField(default=1),
        ),
    ]
