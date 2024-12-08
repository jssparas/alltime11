from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status

from users.models import User


class TestUserSignupLogin(APITestCase):
    url = reverse('otp_view')

    @classmethod
    def setUpTestData(cls):
        User.objects.create(phone_number='9910758837')

    @classmethod
    def tearDownClass(cls):
        cache.clear()
        super(TestUserSignupLogin, cls).tearDownClass()

    def test_1_mobile_not_present(self):
        data = {}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_message = response.json().get("message").get("phone_number")[0]
        self.assertEquals(error_message, "This field is required.")

    def test_2_invalid_mobile(self):
        data = {'phone_number': '9910758827fwefewd'}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_message = response.json().get("message").get("phone_number")[0]
        self.assertEquals(error_message, "Enter a valid phone number.")

    def test_3_new_user_signup(self):
        mobile = '+919910758827'
        data = {'phone_number': mobile, 'is_signup': True}
        otp_generate_response = self.client.post(self.url, data)
        self.assertEquals(otp_generate_response.status_code, status.HTTP_200_OK)
        message = otp_generate_response.json().get("message")
        self.assertEquals(message, "otp sent successfully")
        self.assertEquals(cache.get(f'{mobile}_otp'), '123456')
        self.assertEquals(cache.get(f'{mobile}_otp_count'), 1)

        data = {'phone_number': mobile, 'otp': '123456'}
        otp_validate_response = self.client.post(self.url, data)
        validate_response = otp_validate_response.json()
        self.assertEquals(otp_validate_response.status_code, status.HTTP_200_OK)
        self.assertTrue(validate_response.get("is_new"))
        self.assertTrue(validate_response.get("is_active"))
        self.assertTrue('refresh_token' in validate_response)
        self.assertTrue('access_token' in validate_response)
        self.assertTrue(User.objects.filter(phone_number=mobile).exists())

    def test_4_existing_user_signup(self):
        mobile = '+919910758837'
        data = {'phone_number': mobile, 'is_signup': True}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        message = response.json().get('message').get('user')[0]
        self.assertEquals(message, "user is already signed up, please login")
