from django.db import models
from django.conf import settings

from alltime11.models import BaseModel


class TeamManager(models.Manager):
    pass


class Team(BaseModel):
    uid = models.CharField(unique=True, max_length=40, null=False, blank=False)
    name = models.CharField(max_length=30, null=False, blank=False)
    flag = models.CharField(max_length=200, null=True)

    objects = TeamManager()

    def __repr__(self):
        return f"<Team - id:{self.pk} - uid:{self.uid} - name:{self.name}>"

    def save(self, *args, **kwargs):
        # TODO: add custom saving code here
        super().save(*args, **kwargs)
