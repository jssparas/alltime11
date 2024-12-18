# Generated by Django 4.1 on 2023-10-16 19:16

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cricket', '0003_alter_match_association_id_alter_match_end_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchplayer',
            name='player_credits',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='matchplayer',
            name='player_points',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='matchplayer',
            name='player_rank',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='matchplayer',
            name='player_tournament_points',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='match',
            name='play_status',
            field=models.CharField(choices=[('abandoned', 'Abandoned'), ('rain_delay', 'Rain Delay'), ('in_play', 'In Play'), ('result', 'Result'), ('scheduled', 'Scheduled')], default='abandoned', max_length=20),
        ),
        migrations.AlterField(
            model_name='matchplayer',
            name='batting_stats',
            field=models.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='matchplayer',
            name='bowling_stats',
            field=models.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='matchplayer',
            name='fielding_stats',
            field=models.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='matchplayer',
            name='roles',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=20), null=True, size=5),
        ),
        migrations.AlterField(
            model_name='player',
            name='jersey_name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='player',
            name='legal_name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='player',
            name='name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='player',
            name='seasonal_role',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='player',
            name='skills',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=20), null=True, size=5),
        ),
    ]
