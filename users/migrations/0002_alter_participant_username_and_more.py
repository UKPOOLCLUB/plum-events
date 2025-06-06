# Generated by Django 4.2.21 on 2025-05-12 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_minigolfscorecard'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='username',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterUniqueTogether(
            name='participant',
            unique_together={('username', 'event')},
        ),
    ]
