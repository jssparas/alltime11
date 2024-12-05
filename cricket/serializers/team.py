from rest_framework import serializers

from cricket.models import Team


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['name', 'flag']


class TeamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "uid", "name", "flag"]


class TeamGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'
