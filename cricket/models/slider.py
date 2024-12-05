from django.db import models
from django.conf import settings

from alltime11 import validators
from alltime11.models import BaseModel


class SliderManager(models.Manager):
    pass


class Slider(BaseModel):
    slider_path = models.CharField(max_length=200, null=True)
    deep_link = models.CharField(max_length=250, null=False, blank=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sliders',
                                   validators=[validators.validate_slider_creator])
    is_active = models.BooleanField(default=True)

    objects = SliderManager()

    def __repr__(self):
        return f"<Slider - id:{self.pk} - slider_path:{self.slider_path}>"

    def save(self, *args, **kwargs):
        # TODO: add custom saving code here
        super().save(*args, **kwargs)
