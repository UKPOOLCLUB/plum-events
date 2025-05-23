# Generated by Django 4.2.21 on 2025-05-11 17:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='minigolfscore',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.participant'),
        ),
        migrations.AddField(
            model_name='minigolfgroup',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='golf_groups', to='events.event'),
        ),
        migrations.AddField(
            model_name='minigolfgroup',
            name='players',
            field=models.ManyToManyField(related_name='golf_groups', to='users.participant'),
        ),
        migrations.AddField(
            model_name='minigolfgroup',
            name='scorekeeper',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='kept_scores', to='users.participant'),
        ),
        migrations.AddField(
            model_name='minigolfconfig',
            name='event',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='golf_config', to='events.event'),
        ),
        migrations.AddField(
            model_name='killerconfig',
            name='event',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='killer_config', to='events.event'),
        ),
        migrations.AddField(
            model_name='dartsconfig',
            name='event',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='darts_golf_config', to='events.event'),
        ),
    ]
