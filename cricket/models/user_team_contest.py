from django.db import models
from django.conf import settings

from alltime11.models import BaseModel
from .contest import Contest
from .user_team import UserTeam


class UserTeamContestManager(models.Manager):
    pass


class UserTeamContest(BaseModel):
    user_team = models.ForeignKey(UserTeam, on_delete=models.CASCADE, related_name="contests")
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='userteams')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type_choices = (
        ('unique', 'unique'),
        ('multiple', 'multiple')
    )
    entry_type = models.CharField(max_length=20, choices=type_choices, default='unique')
    rank = models.IntegerField(null=True)

    objects = UserTeamContestManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'contest', 'entry_type'), name='unique_user_contest',
                                    condition=models.Q(entry_type='unique'))
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __repr__(self):
        return f"<UserTeamContest - id:{self.pk} - userteam:{self.user_team.id} - contest:{self.contest.id}>"
