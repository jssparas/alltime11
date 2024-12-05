import logging

import boto3
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth import get_user_model

from utils.helpers import s3_delete_file
from cricket.models import Slider
from common_api.serializers import DashboardSerializer
from cricket.serializers import SliderListSerializer
from users.serializers import UserSerializer

LOG = logging.getLogger('api')
User = get_user_model()


class AdminDashboardView(APIView):
    def get(self, request):
        if not request.user.is_superuser or not request.user.is_staff:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user_ds = DashboardSerializer(request.user)
        transaction_data = {  # need to make dynamic once schema will be ready
            "total_transactions": 0,
            "total_deposits": 0,
            "total_withdrawals": 0
        }
        data = {"users_data": user_ds.data, "transaction_data": transaction_data}
        return Response(data=data, status=status.HTTP_200_OK)


class AdminSliderView(APIView):
    """ create and update """
    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser or not request.user.is_staff:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # get attachment key
        attachment_key = request.data.get("keys")
        if not attachment_key:
            return Response(data={"message": {"slider": ["Invalid Request Format"]}},
                            status=status.HTTP_400_BAD_REQUEST)

        if kwargs.get("pk"):
            try:
                slider = Slider.objects.get(id=kwargs.get("pk"))
            except Slider.DoesNotExist:
                return Response(data={"message": {"slider": ["slider does not exists"]}},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            # create row into db:
            slider = Slider(created_by=request.user)
            try:
                slider.save()
            except Exception as ex:
                print(f"error while saving banner, {ex}")
                return Response(data={"message": {"slider": ["Could not save banner"]}},
                                status=status.HTTP_400_BAD_REQUEST)

        s3 = boto3.client('s3', settings.AWS_REGION)
        key = f"cricket-banners/cricket-banner-{slider.id}/{slider.id}-{attachment_key}"
        try:
            s3_data = s3.generate_presigned_post(settings.ATTACHMENT_BUCKET,  key)
            if s3_data:
                # update into db
                slider.slider_path = key
                slider.deep_link = request.data.get("deep_link", None)
                if "is_active" in request.data:
                    slider.is_active = request.data.get("is_active")
                slider.save()
                return Response(data=s3_data, status=status.HTTP_200_OK)
        except Exception as ex:
            print(f"error while saving banner, {ex}")
            return Response(data={"message": {"slider": [f"Could not fetch s3 data for banner id: {slider.id}"]}},
                            status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        try:
            slider_query = Slider.objects
            if request.user.is_superuser:
                slider_query = slider_query.filter(created_by=request.user)
            else:
                slider_query = slider_query.filter(is_active=True)
            data = {
                "data": {
                    "sliders": SliderListSerializer(slider_query, many=True).data
                }
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as obne:
            # TODO: add logger.error
            return Response(data={"message": {"sliders": ["sliders does not exists"]}},
                            status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        if not request.user.is_superuser or not request.user.is_staff:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            pk = kwargs.get("pk")
            slider = Slider.objects.get(id=pk)
            try:
                resp = s3_delete_file(slider.slider_path)
                slider.delete()
                return Response(data={"message": {"slider": [f"Banner deleted successfully"]}}, status=status.HTTP_200_OK)
            except Exception as ex:
                return Response(data={"message": {"slider": [f"Could not delete file from s3 for banner id: {slider.id}"]}},
                            status=status.HTTP_400_BAD_REQUEST)

        except ObjectDoesNotExist:
            return Response(data={"message": {"slider": ["slider does not exists"]}},
                            status=status.HTTP_404_NOT_FOUND)


class AdminUserUpdateView(APIView):
    def patch(self, request, **kwargs):
        LOG.debug("patch args and kwargs %s", kwargs)
        if not (request.user.is_superuser or request.user.is_staff):
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            user = User.objects.get(uid=kwargs.get("uid"))
            if user.is_superuser or user.is_staff:
                return Response(data={"user": ["cannot update admin user"]}, status=status.HTTP_400_BAD_REQUEST)
            if "is_active" in request.data:
                user.is_active = request.data["is_active"]
            if "is_blocked" in request.data:
                user.is_blocked = request.data["is_blocked"]

            user.save()
            return Response(data={"data": {"user": UserSerializer(user).data}}, status=status.HTTP_200_OK)
        except ValidationError as ve:
            return Response(data={"user": ve}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(data={"user": ["user does not exists"]}, status=status.HTTP_404_NOT_FOUND)
