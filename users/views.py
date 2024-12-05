from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.serializers import ValidationError

from users.models import User
from users.serializers import UserSerializer, UserGetSerializer


class UserView(APIView):

    def get(self, request, uid=None):
        try:
            # for admin 
            if request.user.is_superuser or request.user.is_staff:
                user_query = User.objects.filter(~Q(id=request.user.id))
                if not uid:
                    data = {
                        "data": {
                            "users": UserSerializer(user_query, many=True).data
                        }
                    }
                else:
                    user_query = user_query.filter(uid=uid)
                    data = {
                        "data": {
                            "user": UserSerializer(user_query.get()).data
                        }
                    }

            else:
                user_query = User.objects.filter(phone_number=request.user.phone_number)
                if uid:
                    user_query = user_query.filter(uid=uid)
                user = user_query.get()
                data = {
                    "data": {
                        "user": UserSerializer(user).data
                    }
                }
            return Response(data=data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as obne:
            # TODO: change to logger.error
            return Response(data={"message": {"user": ["user does not exists"]}}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, uid=None):
        try:
            user_query = User.objects.filter(phone_number=request.user.phone_number)
            if uid:
                user_query = user_query.filter(uid=uid)
            user = user_query.get()
        except ObjectDoesNotExist as obne:
            # TODO: change to logger.error
            print("404 user not found", obne)
            return Response(data={"message": {"user": ["user does not exists"]}}, status=status.HTTP_404_NOT_FOUND)

        us = UserSerializer(instance=user, data=request.data, partial=True)
        try:
            us.is_valid(raise_exception=True)
            us.save()
            data = {
                "data": {
                    "user": us.data
                }
            }
            return Response(data=data, status=status.HTTP_202_ACCEPTED)
        except ValidationError as ve:
            # TODO: add logger.error
            print("patch errors", us.errors)
            return Response(data={"message": us.errors}, status=status.HTTP_400_BAD_REQUEST)
