from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status

from users.models import User
from users.tasks import verify_otp

existing_user_mobile = '9910858837'
new_user_mobile = '+919910958847'
inactive_user_mobile = '+919910058857'
blocked_user_mobile = '+919910358867'


class TestUserSignupLogin(APITestCase):
    url = reverse('otp_view')

    @classmethod
    def setUpTestData(cls):
        User.objects.create(phone_number=existing_user_mobile)
        User.objects.create(phone_number=inactive_user_mobile, is_active=False)
        User.objects.create(phone_number=blocked_user_mobile, is_blocked=True)

    def tearDown(self) -> None:
        cache.clear()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        cache.clear()
        super(TestUserSignupLogin, cls).tearDownClass()

    def test_1_empty_data(self):
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
        data = {'phone_number': new_user_mobile, 'is_signup': True}
        otp_generate_response = self.client.post(self.url, data)
        self.assertEquals(otp_generate_response.status_code, status.HTTP_200_OK)
        message = otp_generate_response.json().get("message")
        self.assertEquals(message, "otp sent successfully")
        self.assertEquals(cache.get(f'{new_user_mobile}_otp'), '123456')
        self.assertEquals(cache.get(f'{new_user_mobile}_otp_count'), 1)

        data = {'phone_number': new_user_mobile, 'otp': '123456'}
        otp_validate_response = self.client.post(self.url, data)
        validate_response = otp_validate_response.json()
        self.assertEquals(otp_validate_response.status_code, status.HTTP_200_OK)
        self.assertTrue(validate_response.get("is_new"))
        self.assertTrue(validate_response.get("is_active"))
        self.assertTrue('refresh_token' in validate_response)
        self.assertTrue('access_token' in validate_response)
        self.assertTrue(User.objects.filter(phone_number=new_user_mobile).exists())

    def test_4_existing_user_signup(self):
        data = {'phone_number': existing_user_mobile, 'is_signup': True}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        message = response.json().get('message').get('user')[0]
        self.assertEquals(message, "user is already signed up, please login")

    def test_5_new_user_login(self):
        data = {'phone_number': new_user_mobile}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        message = response.json().get("message").get("user")[0]
        self.assertEquals(message, "account does not exists, please signup")

    def test_6_existing_user_login(self):
        data = {'phone_number': existing_user_mobile}
        otp_generate_response = self.client.post(self.url, data)
        self.assertEquals(otp_generate_response.status_code, status.HTTP_200_OK)
        message = otp_generate_response.json().get("message")
        self.assertEquals(message, "otp sent successfully")
        self.assertEquals(cache.get(f'{existing_user_mobile}_otp'), '123456')
        self.assertEquals(cache.get(f'{existing_user_mobile}_otp_count'), 1)

        data = {'phone_number': existing_user_mobile, 'otp': '123456'}
        otp_validate_response = self.client.post(self.url, data)
        validate_response = otp_validate_response.json()
        self.assertEquals(otp_validate_response.status_code, status.HTTP_200_OK)
        self.assertFalse(validate_response.get("is_new"))
        self.assertTrue(validate_response.get("is_active"))
        self.assertTrue('refresh_token' in validate_response)
        self.assertTrue('access_token' in validate_response)

    def test_7_blocked_user_login(self):
        data = {'phone_number': blocked_user_mobile}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        message = response.json().get("message").get("user")[0]
        self.assertEquals(message, "phone_number is blocked on the platform")

    def test_8_inactive_user_login(self):
        data = {'phone_number': inactive_user_mobile}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        message = response.json().get("message").get("user")[0]
        self.assertEquals(message, "user is deleted on the platform")

    def test_9_otp_request_limit(self):
        data = {'phone_number': existing_user_mobile}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(cache.get(f'{existing_user_mobile}_otp_count'), 1)
        verify_otp(existing_user_mobile, '123456')

        # 2nd time
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(cache.get(f'{existing_user_mobile}_otp_count'), 2)
        verify_otp(existing_user_mobile, '123456')

        # 3nd time
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(cache.get(f'{existing_user_mobile}_otp_count'), 3)
        verify_otp(existing_user_mobile, '123456')

        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        error_message = response.json().get("message").get("otp")[0]
        self.assertEquals(error_message, "otp attempts exceeded, try again after 15 mins")

    def test_10_invalid_otp_verification(self):
        data = {'phone_number': existing_user_mobile}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        data = {'phone_number': existing_user_mobile, 'otp': '111111'}
        response = self.client.post(self.url, data)
        self.assertEquals(response.status_code, status.HTTP_401_UNAUTHORIZED)
        message = response.json().get("message").get("otp")[0]
        self.assertEquals(message, "otp verification failed")
