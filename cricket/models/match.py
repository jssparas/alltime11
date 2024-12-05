from django.db import models

from alltime11.models import BaseModel
from alltime11 import validators, constants
from .team import Team
from .tournament import Tournament
from .player import Player


class MatchManager(models.Manager):
    pass


class Match(BaseModel):
    uid = models.CharField(unique=True, max_length=50, null=False, blank=False)
    name = models.CharField(max_length=200, null=False, blank=False)
    short_name = models.CharField(max_length=50, null=False, blank=False)
    subtitle = models.CharField(max_length=50, null=True, blank=False)
    status_choices = (
        (constants.MATCH_STATUS_NOT_STARTED, 'Not Started'),
        (constants.MATCH_STATUS_STARTED, 'Started'),
        (constants.MATCH_STATUS_COMPLETED, 'Completed'),
    )
    status = models.CharField(max_length=20, choices=status_choices, default=constants.MATCH_STATUS_NOT_STARTED)
    start_date = models.DateTimeField(null=False)
    end_date = models.DateTimeField(null=True)
    association_id = models.CharField(max_length=200, null=False, blank=False, db_index=True)
    gender = models.CharField(max_length=10)
    venue_name = models.CharField(max_length=200, null=False, blank=False)
    venue_city = models.CharField(max_length=20, null=False, blank=False)
    venue_country = models.CharField(max_length=2, null=True, blank=False, validators=[validators.validate_country_code])
    play_choices = (
        ('abandoned', 'Abandoned'),
        ('rain_delay', 'Rain Delay'),
        ('in_play', 'In Play'),
        ('result', 'Result'),
        ('scheduled', 'Scheduled')
    )
    play_status = models.CharField(max_length=20, choices=play_choices, default='abandoned')
    is_date_confirmed = models.BooleanField(default=False)
    is_venue_confirmed = models.BooleanField(default=False)
    title = models.CharField(max_length=100, null=True, blank=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    team_a = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='a_matches')
    team_b = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='b_matches')
    format_choices = (
        ('t20', 'Twenty 20'),
        ('oneday', 'One Day'),
        ('test', 'Test Match'),
    )
    match_format = models.CharField(max_length=20, choices=format_choices, default='t20')
    toss_info = models.JSONField(null=True)
    target_info = models.JSONField(null=True)
    first_batting = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name='first_bat_matches')
    team_a_score = models.JSONField(null=True)
    team_b_score = models.JSONField(null=True)
    pom = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, related_name='pom_matches')
    winner = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name='won_matches')
    win_choices = (
        ('runs', 'runs'),
        ('wickets', 'wickets'),
    )
    win_type = models.CharField(max_length=10, choices=win_choices, null=True, blank=False)
    win_message = models.CharField(max_length=200, null=True, blank=False)
    delayed_time = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)

    objects = MatchManager()

    def __repr__(self):
        return f"<Match - id:{self.pk} - uid:{self.uid} - name:{self.name}>"

    def save(self, *args, **kwargs):
        if self.team_a.id == self.team_b.id:
            raise ValueError("Both team cannot be same")
        if self.tournament.association_id != self.association_id:
            raise ValueError("Match's association is different than Tournament's")
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("Match's end date should be greater than start date")
        super().save(*args, **kwargs)

    @classmethod
    def parse_team_score_data(score_data):
        team_score_data = {
            "runs": score_data.get("score").get("runs", None),
            "balls": score_data.get("score").get("balls", None),
            "wickets": score_data.get("wickets", None),
            "score_str": score_data.get("score_str", None),
            "extra_runs": score_data.get("extra_runs").get("extra", None),
            "wide": score_data.get("extra_runs").get("wide", None),
            "leg_bye": score_data.get("extra_runs").get("leg_bye", None),
            "no_balls": score_data.get("extra_runs").get("no_balls", None),
            "penalty": score_data.get("extra_runs").get("penalty", None),
            "bye": score_data.get("extra_runs").get("bye", None)
        }
        return team_score_data
