from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status


class TestSignUp(APITestCase):
    url = reverse('otp_view')
    # TODO: 1. generate otp -> send_otp -> check status -> check token, get details, check new, assert on new fields


class TestLogin(APITestCase):
    url = reverse('otp_view')
    # TODO: 1. user above mobile, generate otp -> send_otp -> check status -> check token, get details, check new, assert on new fields


class TestTokenRefresh(APITestCase):
    url = reverse('otp_view')
