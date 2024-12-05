from functools import partial

from django.db import models
from django.conf import settings

from alltime11.models import BaseModel
from alltime11 import validators, constants
from utils.shortuuid import generate


class RewardManager(models.Manager):
    pass


class Reward(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rewards')
    type_choices = (
        (constants.RC_WALLET, 'Add wallet balance bonus'),
        (constants.RC_CONTEST, 'Join contest bonus'),
        (constants.RC_SIGNUP, 'Signup reward')
    )
    reward_type = models.CharField(max_length=15, choices=type_choices)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_rewards',
                                   validators=[validators.validate_contest_creator])
    is_active = models.BooleanField()
    discount_percentage = models.DecimalField(max_digits=4, decimal_places=2, default=5.0)
    discount_amount = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    max_discount_amount = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    max_redeem_count = models.IntegerField(default=1)
    redeem_count = models.IntegerField(default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status_choices = (
        (constants.REWARD_PENDING, 'Pending'),
        (constants.REWARD_APPLIED, 'Applied')
    )
    status = models.CharField(max_length=20, choices=status_choices, default=constants.REWARD_PENDING)
    code = models.CharField(default=partial(generate, prefix='C', max_length=10), max_length=10, db_index=True)

    objects = RewardManager()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __repr__(self):
        return f"<Reward - id:{self.pk} - user:{self.user}>"

    def __str__(self):
        return f"<Reward - id:{self.pk} - match:{self.user}>"
