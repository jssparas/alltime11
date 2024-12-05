from django.db import models

from alltime11 import validators
from alltime11.models import BaseModel


class TournamentManager(models.Manager):
    pass


class Tournament(BaseModel):
    sport_choices = (
        ('cricket', 'Cricket'),
        ('kabaddi', 'Kabaddi'),
        ('football', 'Football'),
    )
    uid = models.CharField(unique=True, max_length=200, null=False, blank=False)
    name = models.CharField(max_length=200, null=False, blank=False)
    short_name = models.CharField(max_length=200, null=False, blank=False)
    sport_type = models.CharField(max_length=10, choices=sport_choices, default='cricket')
    association_id = models.CharField(max_length=200, null=False, blank=False, db_index=True)
    gender = models.CharField(max_length=10)
    is_date_confirmed = models.BooleanField(default=False)
    is_venue_confirmed = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True)
    last_scheduled_match_date = models.DateTimeField(null=True)
    country = models.CharField(max_length=2, null=True, blank=False, validators=[validators.validate_country_code])

    objects = TournamentManager()

    def __repr__(self):
        return f"<Tournament - id:{self.pk} - uid:{self.uid} - name:{self.name}>"

    def save(self, *args, **kwargs):
        # TODO: add custom saving code here
        super().save(*args, **kwargs)
