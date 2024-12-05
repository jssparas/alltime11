from rest_framework import serializers

from cricket.models import Tournament


class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ['name']

class TournamentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ["id", "uid", "name", "short_name", "sport_type", "gender",
                  "start_date", "country", "last_scheduled_match_date"]


class TournamentGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = '__all__'