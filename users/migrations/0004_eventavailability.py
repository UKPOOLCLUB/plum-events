# Generated by Django 4.2.21 on 2025-06-29 01:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_participant_kept_scores'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventAvailability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('status', models.CharField(choices=[('available', 'Available'), ('full', 'Fully Booked'), ('blackout', 'Blackout Date')], default='available', max_length=10)),
            ],
        ),
    ]
