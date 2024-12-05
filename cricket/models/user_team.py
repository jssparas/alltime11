from django.db import models
from django.conf import settings
from django.core.validators import ValidationError

from alltime11.models import BaseModel
from alltime11 import validators
from .match import Match
from .match_player import MatchPlayer


class UserTeamManager(models.Manager):
    pass


class UserTeam(BaseModel):
    name = models.CharField(max_length=5, default='T1')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='user_teams')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teams')
    players = models.JSONField()
    captain = models.ForeignKey(MatchPlayer, on_delete=models.SET_NULL, null=True, related_name='matches_as_captain')
    vice_captain = models.ForeignKey(MatchPlayer, on_delete=models.SET_NULL, null=True,
                                     related_name='matches_as_vice_captain')
    batsman_count = models.IntegerField(validators=[validators.validate_batsman_count])
    bowler_count = models.IntegerField(validators=[validators.validate_bowler_count])
    all_rounder_count = models.IntegerField(validators=[validators.validate_all_rounder_count])
    keeper_count = models.IntegerField(validators=[validators.validate_keeper_count])

    objects = UserTeamManager()

    @property
    def points(self):
        total_points = 0
        for player_id in self.players:
            total_points += MatchPlayer.objects.filter(id=player_id).values("player_points")[0].get("player_points")

        return total_points

    def save(self, *args, **kwargs):
        total_player_count = self.batsman_count + self.bowler_count + self.all_rounder_count + self.keeper_count
        if total_player_count != 11:
            raise ValidationError(f"total player count is {total_player_count}, cannot form team")

        # TODO: add check on players, every key in the json must be an ID from matchplayer table
        #  django query exists and length type something
        super().save(*args, **kwargs)

    def __repr__(self):
        return f"<UserTeam - id:{self.pk} - user:{self.user.uid}>"
