import requests
import logging
import json
import base64
from django.conf import settings

logger = logging.getLogger('api')
def send_sms(mobile_no="", sms_text=""): # mobile no can be list or single mobile
    '''
        SMS Country API for sending SMS to user
    '''
    try:
        token = f'{settings.SMS_COUNTRY_AUTH_KEY}:{settings.SMS_COUNTRY_AUTH_TOKEN}'
        token = base64.b64encode(token.encode())
        headers = {
            "Authorization": f'Basic {token.decode()}',
            "Content-Type": "application/json"
        }
        url = settings.SMS_COUNTRY_API_URL.replace("{AUTH_KEY}", settings.SMS_COUNTRY_AUTH_KEY)
        payload = {
                    "Text": sms_text,
                    "SenderId": settings.SMS_COUNTRY_SENDER_ID,
                    "DRNotifyUrl": "", # to check sms status set callback url
                    "DRNotifyHttpMethod": "", # need to set if DRNotifyUrl
                    "Tool":"API"
                }
        if isinstance(mobile_no, list): # to send sms to multiple users
            payload["Numbers"] = mobile_no
        else:
            payload["Number"] = mobile_no
        logger.info(f"SMS Api Request Payload {payload}")
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
            logger.info(f"SMS Api Response Payload {resp}")
            if resp.ok:
                response = resp.json()
                if response.get("Success"):
                    return True, response.get("Message")
                return False, response.get("Message")
            logger.error("Error in sending SMS, Error: %s", resp.text)
            return False, resp.text
        except (requests.Timeout, requests.ConnectionError):
            logger.error('Timeout or ConnectionError exception occurred during sending sms')
            raise
    except Exception as ex:
        logger.error("Could not send sms to user mobile: %s, Error: %s", str(mobile_no),ex)
        raise ex
