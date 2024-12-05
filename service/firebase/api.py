import requests
import time
import json
import google.auth.transport.requests
from google.oauth2 import service_account

from django.conf import settings


def fcm_send_push_notification(**kwargs):
    ''' TO Do logging
        Firebase API for sending push notification to user
    '''
    try:
        headers = {
            "Authorization": f'Bearer {get_google_oauth2_access_token()}'
        }
        url = f'{settings.FIREBASE_BASE_URL}/v1/projects/{settings.FIREBASE_PROJECT_ID}/messages:send'
        payload = {
            "message": {
                "token": kwargs.get("firebase_user_token"),
                "notification": {"body": kwargs.get("msg_body"), "title": kwargs.get("msg_title")}
            }
        }
        #print("payload", payload)
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
            print(f"resp: {resp}")
            if resp.ok:
                response = resp.json()
                if "name" in response:
                    return True, ""
            else:
                print(f"Error in sending FCM push notification, Error: {resp.text}")
                return False, resp.text
        except (requests.Timeout, requests.ConnectionError):
            print('Timeout or ConnectionError exception occurred during firebase api calling')
            raise
    except Exception as ex:
        print(f"Could not send FCM push notification to user, Error: {ex}")
        raise ex


def get_google_oauth2_access_token():
    """
        Retrieve a valid oauth2 access token that can be used to authorize FCM requests.
        return: Access token.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(settings.FIREBASE_SERVICE_ACCOUNT_FILE,\
                            scopes=[settings.FIREBASE_SCOPE_URL])
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        return credentials.token
    except Exception as ex:
        print(f"Could not generate google oauth token, Error:{ex}")
        raise