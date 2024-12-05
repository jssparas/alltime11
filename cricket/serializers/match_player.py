from rest_framework import serializers

from cricket.models import MatchPlayer, Player
from .team import TeamSerializer
from .player import PlayerSerializer


class MatchPlayerSerializer(serializers.ModelSerializer):
    team = TeamSerializer()
    player = PlayerSerializer()

    class Meta:
        model = MatchPlayer
        fields = '__all__'


class SingleMatchPlayerSerializer(serializers.ModelSerializer):

    class Meta:
        model = MatchPlayer
        fields = '__all__'


class MatchPlayerScoreCardSerializer(serializers.ModelSerializer):
    player_name = serializers.SerializerMethodField()

    def get_player_name(self, obj):
        return obj.player.name
            
    class Meta:
        model = MatchPlayer
        fields = ('player_name', 'batting_stats', 'bowling_stats', 'team_id', 'is_captain',
                    "is_keeper", "is_bowler", "is_batsman", "is_all_rounder", "playing_order"
                )
