from datetime import datetime

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from alltime11 import constants
from cricket.models import Tournament
from cricket.serializers import TournamentListSerializer, TournamentGetSerializer


class TournamentListView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            if not request.user.is_superuser or not request.user.is_staff:
                return Response(status=status.HTTP_404_NOT_FOUND)
            tournament_query = Tournament.objects.all()
            data = {
                "data": {
                    "tournaments": TournamentListSerializer(tournament_query, many=True).data
                }
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as obne:
            # TODO: add logger.error
            return Response(data={"message": {"tournaments": ["tournaments does not exists"]}},
                            status=status.HTTP_404_NOT_FOUND)


class TournamentRetrieveView(RetrieveAPIView):
    queryset = Tournament.objects.all()
    serializer_class = TournamentGetSerializer

    def retrieve(self, request, *args, **kwargs):
        tournament = self.get_object()
        ts = self.get_serializer(tournament)
        tournament_data = ts.data
        return Response({'data': {'tournament': tournament_data}}, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser or not request.user.is_staff:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return self.retrieve(request, *args, **kwargs)
