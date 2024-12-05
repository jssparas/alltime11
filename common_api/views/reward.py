from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import ObjectDoesNotExist, F, Q
from django.utils import timezone

from alltime11 import constants
from common_api.serializers import RewardSerializer
from common_api.models import Reward


class RewardListCreateAPIView(ListCreateAPIView):
    serializer_class = RewardSerializer
    queryset = Reward.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if not (user.is_superuser or user.is_staff):
            queryset = queryset.filter(Q(status=constants.REWARD_PENDING) |
                                       Q(redeem_count__lt=F('max_redeem_count')))

        return queryset

    def filter_queryset(self, queryset):
        user_id = self.request.GET.get("user")
        admin_id = self.request.GET.get("admin")
        re_status = self.request.GET.get("status")
        if user_id and user_id.isdigit():
            queryset = queryset.filter(user__id=user_id)
        if admin_id and admin_id.isdigit():
            queryset = queryset.filter(created_by__id=admin_id)
        if status and status in {constants.REWARD_PENDING, constants.REWARD_APPLIED}:
            queryset = queryset.filter(status=re_status)
        return super().filter_queryset(queryset.order_by('-start_date'))

    def get(self, request, *args, **kwargs):
        response = self.list(request, *args, **kwargs)
        response.data = {
            'data': {
                'rewards': response.data
            }
        }
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(**kwargs)
        headers = self.get_success_headers(serializer.data)
        return Response({'data': {'reward': serializer.data}}, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.is_staff):
            return Response(status=status.HTTP_404_NOT_FOUND)
        kwargs["created_by"] = self.request.user
        return self.create(request, *args, **kwargs)


class RewardApplyAPIView(APIView):
    def post(self, request):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Response(status=status.HTTP_404_NOT_FOUND)
        code = request.data.get("code")
        if not code:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            reward = Reward.objects.get(user__id=self.request.user.id, code=code)
        except ObjectDoesNotExist:
            return Response(data={'non_field_errors': ['reward not found']}, status=status.HTTP_400_BAD_REQUEST)
        if reward.end_date.date() < timezone.now().date():
            return Response(data={'non_field_errors': ['reward is from past date']}, status=status.HTTP_400_BAD_REQUEST)
        if reward.status == constants.REWARD_APPLIED and reward.redeem_count == reward.max_redeem_count:
            return Response(data={'non_field_errors': ['reward is already applied']},
                            status=status.HTTP_400_BAD_REQUEST)

        reward.status = constants.REWARD_APPLIED
        reward.redeem_count += 1
        reward.save()
        return Response(data={'message': 'reward applied'}, status=status.HTTP_200_OK)
