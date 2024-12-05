from rest_framework.generics import RetrieveAPIView

from cricket.models import MatchPlayer
from cricket.serializers import SingleMatchPlayerSerializer


class MatchPlayerRetrieveView(RetrieveAPIView):
    queryset = MatchPlayer.objects.all()
    serializer_class = SingleMatchPlayerSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
