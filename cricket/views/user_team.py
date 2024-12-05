from django.db.models import ObjectDoesNotExist
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from cricket.models import Match, UserTeam
from cricket.serializers import UserTeamSerializer, UserTeamPlayerStatusSerializer


class UserTeamListCreateView(ListCreateAPIView):
    queryset = UserTeam.objects.all()
    serializer_class = UserTeamSerializer

    def filter_queryset(self, queryset):
        queryset = queryset.filter(user=self.request.user)
        return super().filter_queryset(queryset)

    def get(self, request, *args, **kwargs):
        try:
            match = Match.objects.get(pk=kwargs.get("match_id"))
        except ObjectDoesNotExist as obne:
            return Response(data={"message": {"userteams": ["match does not exists"]}},
                            status=status.HTTP_404_NOT_FOUND)
        self.queryset = UserTeam.objects.filter(match=match)
        response = self.list(request, *args, **kwargs)
        response.data = {
            'data': {
                'user_teams': response.data
            }
        }
        return response

    def create(self, request, *args, **kwargs):
        if request.user.is_superuser or request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        match_id = kwargs.get("match_id")
        serializer = self.get_serializer(data={**request.data, **{"match_id": match_id,
                                                                  'user_id': self.request.user.id}})
        serializer.is_valid(raise_exception=True)
        serializer.save(**kwargs)
        headers = self.get_success_headers(serializer.data)
        return Response({'data': {'user_team': serializer.data}}, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        kwargs["user"] = request.user
        return self.create(request, *args, **kwargs)


class UserTeamRetrieveUpdateView(RetrieveUpdateAPIView):
    queryset = UserTeam.objects.all()
    serializer_class = UserTeamSerializer

    def filter_queryset(self, queryset):
        queryset = queryset.filter(user=self.request.user)
        return super().filter_queryset(queryset)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'data': {
                'user_team': serializer.data
            }
        })

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        response.data = {
            'data': {
                'user_team': response.data
            }
        }
        return response

class UserTeamPlayerStatusView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            queryset = UserTeam.objects.get(id=kwargs.get("pk"), user=request.user, match_id=kwargs.get("match_id"))
            try:
                serializer = UserTeamPlayerStatusSerializer(queryset, many=False)
                return Response({
                    'data': serializer.data
                })
            except Exception as ex:
                print("error", ex)
                return Response(data={"message": {"match": ["Colud not fetch User Team player status data"]}},
                                status=status.HTTP_400_BAD_REQUEST)
        except UserTeam.DoesNotExist:
            # print(f"Error in get match score card api:{ex}")
            return Response(data={"message": {"userteam": ["UserTeam not found"]}},
                            status=status.HTTP_404_NOT_FOUND)
