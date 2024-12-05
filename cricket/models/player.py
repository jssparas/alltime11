from django.db import models
from django.contrib.postgres.fields import ArrayField

from alltime11.models import BaseModel
from alltime11 import validators


class PlayerManager(models.Manager):
    pass


class Player(BaseModel):
    uid = models.CharField(unique=True, max_length=50, null=False, blank=False)
    name = models.CharField(max_length=50, null=False, blank=False)
    gender_choices = (
        ('M', "male"),
        ('F', "female")
    )
    gender = models.CharField(max_length=1, choices=gender_choices, null=False, default='M')
    nationality = models.CharField(max_length=2, null=True, blank=False, validators=[validators.validate_country_code])
    date_of_birth = models.DateField(null=True)
    seasonal_role = models.CharField(max_length=20, null=False)
    batting_style = models.CharField(max_length=15, null=False)
    bowling_style = models.CharField(max_length=50, null=True) # need to ask
    skills = ArrayField(models.CharField(max_length=20), null=True, size=5)
    jersey_name = models.CharField(max_length=50, null=False, blank=False)
    legal_name = models.CharField(max_length=200, null=False, blank=False)
    # TODO: add profile_picture

    objects = PlayerManager()

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def __repr__(self):
        return f"<Player - id:{self.pk} - name:{self.name} - nationality:{self.nationality}>"
