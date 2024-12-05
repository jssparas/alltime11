from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListCreateAPIView

from cricket.models import UserTeamContest
from cricket.serializers import UserTeamContestSerializer


class UserTeamContestListCreate(ListCreateAPIView):
    queryset = UserTeamContest.objects.all()
    serializer_class = UserTeamContestSerializer

    def filter_queryset(self, queryset):
        contest_id = self.request.GET.get("contest")
        # queryset = queryset.filter(user=self.request.user)
        if contest_id and contest_id.isdigit():
            queryset = queryset.filter(contest__id=contest_id)
        return super().filter_queryset(queryset.order_by('rank'))

    def get(self, request, *args, **kwargs):
        response = self.list(request, *args, **kwargs)
        response.data = {
            'data': {
                'contest_teams': response.data
            }
        }
        return response

    def post(self, request, *args, **kwargs):
        # request.data["user_id"] = self.request.user.id
        if request.user.is_superuser or request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        response = self.create(request, *args, **kwargs)
        response.data = {
            'data': {
                'contest_team': response.data
            }
        }
        return response
