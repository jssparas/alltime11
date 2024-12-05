from django.db import models
from django.conf import settings

from alltime11.models import BaseModel
from alltime11 import validators, constants
from cricket.models import Tournament
from cricket.models import Match


class ContestManager(models.Manager):
    pass


class Contest(BaseModel):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='contests')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='contests')
    type_choices = (
        ('head_to_head', 'Head To Head'),
        ('medium', 'Medium Contest'),
        ('mega', 'Mega Contest'),
        ('takes_all', 'Winner takes all'),
        ('take_back', 'Take back'),
    )
    contest_type = models.CharField(max_length=15, choices=type_choices)
    name = models.CharField(max_length=20, blank=False, db_index=True)
    prize = models.DecimalField(max_digits=10, decimal_places=2)
    entry_fees = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contests',
                                   validators=[validators.validate_contest_creator])
    is_active = models.BooleanField()
    no_of_teams = models.IntegerField()
    discount_percentage = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    is_private = models.BooleanField(default=False)
    prize_distribution = models.JSONField(null=True)
    status_choices = (
        (constants.CONTEST_STATUS_NOT_STARTED, 'Not Started'),
        (constants.CONTEST_STATUS_STARTED, 'Started'),
        (constants.CONTEST_STATUS_COMPLETED, 'Completed'),
    )
    status = models.CharField(max_length=20, choices=status_choices, default=constants.CONTEST_STATUS_NOT_STARTED)
    is_featured = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('match', 'name'), name='unique_contest_name_match')
        ]

    objects = ContestManager()

    @property
    def entries_left(self):
        from cricket.models import UserTeamContest
        entries_qs = UserTeamContest.objects.filter(contest__id=self.pk).values('contest'). \
            annotate(count=models.Count('contest'))
        contest_entries = entries_qs[0]['count'] if entries_qs else 0

        return self.no_of_teams - contest_entries

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __repr__(self):
        return f"<Contest - id:{self.pk} - match:{self.match.id} - type:{self.contest_type}>"

    def __str__(self):
        return f"<Contest - id:{self.pk} - match:{self.match.id} - type:{self.contest_type}>"
