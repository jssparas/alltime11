from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status

from workers.otp import verify_otp


class TestOtp(APITestCase):
    url = reverse('otp_view')

    @classmethod
    def tearDownClass(cls):
        cache.clear()
        super(TestOtp, cls).tearDownClass()

    def test_1_no_mobile_otp_generate(self):
        data = {}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_message = response.json().get("message").get("phone_number")[0]
        self.assertEquals(error_message, "This field is required.")

    def test_2_invalid_mobile_otp_generate(self):
        data = {'phone_number': '9910758827fwefewd'}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_message = response.json().get("message").get("phone_number")[0]
        self.assertEquals(error_message, "Enter a valid phone number.")

    def test_3_valid_mobile_otp_generate(self):
        mobile = '+919910758827'
        data = {'phone_number': mobile}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        error_message = response.json().get("message")
        self.assertEquals(error_message, "otp sent successfully")

        self.assertEquals(cache.get(f'{mobile}_otp'), '123456')
        self.assertEquals(cache.get(f'{mobile}_otp_count'), 1)

    def test_4_otp_request_limit(self):
        mobile = '+919910758828'
        data = {'phone_number': mobile}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(cache.get(f'{mobile}_otp_count'), 1)
        verify_otp(mobile, '123456')

        # 2nd time
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(cache.get(f'{mobile}_otp_count'), 2)
        verify_otp(mobile, '123456')

        # 3nd time
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(cache.get(f'{mobile}_otp_count'), 3)
        verify_otp(mobile, '123456')

        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        error_message = response.json().get("message").get("otp")[0]
        self.assertEquals(error_message, "otp attempts exceeded, try again after 15 mins")
