from rest_framework import serializers

from utils.helpers import s3_get_presigned_urls
from cricket.models import Slider


class SliderListSerializer(serializers.ModelSerializer):
    slider_path = serializers.SerializerMethodField()

    def get_slider_path(self, obj):
        return s3_get_presigned_urls(obj.slider_path)

    class Meta:
        model = Slider
        fields = ("id", "slider_path", "deep_link", "is_active")