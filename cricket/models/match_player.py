from django.core.validators import ValidationError
from django.db import models
from django.contrib.postgres.fields import ArrayField

from alltime11.models import BaseModel
from .team import Team
from .match import Match
from .player import Player


class MatchPlayerManager(models.Manager):
    pass


class MatchPlayer(BaseModel):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='match_players')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_players')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    is_playing = models.BooleanField(default=False)
    is_captain = models.BooleanField(default=False)
    is_vice_captain = models.BooleanField(default=False)
    is_keeper = models.BooleanField(default=False)
    is_batsman = models.BooleanField(default=False)
    is_bowler = models.BooleanField(default=False)
    is_all_rounder = models.BooleanField(default=False)
    playing_order = models.IntegerField()
    batting_stats = models.JSONField(null=True)
    bowling_stats = models.JSONField(null=True)
    fielding_stats = models.JSONField(null=True)
    roles = ArrayField(models.CharField(max_length=20), null=True, size=5)
    player_points = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    player_tournament_points = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    player_credits = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    player_rank = models.IntegerField(null=True)

    objects = MatchPlayerManager()

    def save(self, *args, **kwargs):
        is_captain = kwargs.get("is_captain") or self.is_captain
        is_vice_captain = kwargs.get("is_vice_captain") or self.is_vice_captain
        is_keeper = kwargs.get("is_keeper") or self.is_keeper
        is_batsman = kwargs.get("is_batsman") or self.is_batsman
        is_bowler = kwargs.get("is_bowler") or self.is_bowler
        is_all_rounder = kwargs.get("is_all_rounder") or self.is_all_rounder

        if (is_batsman and is_bowler) or (is_batsman and is_all_rounder) or (is_bowler and is_all_rounder):
            raise ValidationError("only of the attributes can be true - is_batsman, is_bowler, is_all_rounder")
        if not (is_batsman or is_bowler or is_all_rounder):
            raise ValidationError("one of the attributes should be true - is_batsman, is_bowler, is_all_rounder")

        if is_keeper and not is_batsman:
            raise ValidationError("if is_keeper is true then is_batsman must be true")

        if is_captain and is_vice_captain:
            raise ValidationError("only of the attributes can be true - is_captain, is_vice_captain")

        super().save(*args, **kwargs)

    def __repr__(self):
        return f"<MatchPlayer - id:{self.pk} - order:{self.playing_order}>"

    @classmethod
    def is_player_credits_updated(cls, match_id):
        is_credit_upated = all([True if match_player.player_credits is not None and match_player.player_credits > 0 \
                                else False for match_player in cls.objects.filter(match_id=match_id)])
        return is_credit_upated

    @classmethod
    def is_player_tournament_points_updated(cls, match_id):
        is_point_upated = all([True if match_player.player_tournament_points or (match_player.player_tournament_points is not None and \
                            match_player.player_tournament_points == 0.00) else False for match_player in \
                            cls.objects.filter(match_id=match_id)])
        return is_point_upated
