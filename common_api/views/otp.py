import os

from django.core.cache import cache
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes, authentication_classes
from rest_framework import status

from common_api.serializers import OtpSerializer
from users.serializers import UserSerializer
from users.models import User
from users import tasks as otp_worker

class OtpView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        os = OtpSerializer(data=request.data)
        if not os.is_valid():
            # raise error
            return Response(data={"message": os.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            # mobile = os.validated_data.get("phone_number").as_e164
            mobile = request.data.get("phone_number")
            otp = os.validated_data.get("otp")
            via_ref_code = os.validated_data.get("via_referral_code")
            is_signup = os.validated_data.get("is_signup")
            firebase_token = os.validated_data.get("firebase_token")
            if not otp:
                # 1. otp is not present in the data
                user = list(User.objects.filter(phone_number=mobile).values('is_blocked', 'is_active'))
                if user:
                    is_blocked = user[0].get('is_blocked')
                    is_active = user[0].get('is_active')
                    message = None
                    if is_blocked:
                        message = {"user": ["phone_number is blocked on the platform"]}
                    elif not is_active:
                        message = {"user": ["user is deleted on the platform"]}
                    elif is_signup is True:
                        message = {"user": ["user is already signed up, please login"]}
                    if message:
                        return Response(data={"message": message},
                                        status=status.HTTP_403_FORBIDDEN)
                else:
                    if is_signup is False:
                        return Response(data={"message": {"user": ["account does not exists, please signup"]}},
                                        status=status.HTTP_403_FORBIDDEN)
                if otp_worker.can_send_otp(mobile):
                    # case 1.1: otp can be sent
                    try:
                        otp = otp_worker.send_otp.delay(mobile)
                    except Exception as ex:
                        return Response(data={'message': str(ex)}, status=status.HTTP_400_BAD_REQUEST)
                    if not user and via_ref_code:
                        cache.set(f"{mobile}_via_ref_code", via_ref_code, timeout=5*61)
                    return Response(data={'message': "otp sent successfully"}, status=status.HTTP_200_OK)
                else:
                    # case 1.2: otp can't be sent
                    return Response(data={'message': {"otp": ["otp attempts exceeded, try again after 15 mins"]}},
                                    status=status.HTTP_403_FORBIDDEN)
            else:
                # case 2: otp is present, verify it
                is_verified = otp_worker.verify_otp(mobile, otp)
                if not is_verified:
                    return Response(data={'message': {"otp": ["otp verification failed"]}},
                                    status=status.HTTP_401_UNAUTHORIZED)
                else:
                    is_new = False
                    user = User.objects.filter(phone_number=mobile).first()
                    if not user:
                        is_new = True
                        user = User(phone_number=mobile, via_referral_code=via_ref_code)
                        via_ref_code = cache.get(f"{mobile}_via_ref_code")
                        if via_ref_code:
                            user.via_referral_code = via_ref_code
                            cache.delete(f"{mobile}_via_ref_code")
                        user.save()
                    # save firebase user device token
                    user.firebase_token = firebase_token
                    user.save()
                    us = UserSerializer(user)
                    token = RefreshToken.for_user(user)
                    data = {**us.data, 'refresh_token': str(token), 'access_token': str(token.access_token),
                            'is_new': is_new}
                    return Response(data=data, status=status.HTTP_200_OK)