import sys
import random
import string
import logging

from django.core.cache import cache
from celery import shared_task

from django.conf import settings
from service.smscountry.api import send_sms
from service.smscountry.constants import *

high_logger = logging.getLogger('celery.high')
OTP_COUNT = "otp_count"
OTP = "otp"


def can_send_otp(mobile):
	if settings.ENVIRONMENT != 'prod' and 'test' not in sys.argv:
		return True
	otp_count = cache.get(f"{mobile}_{OTP_COUNT}", 0)
	if otp_count < 3:
		return True
	else:
		return False
@shared_task(queue='high')
def send_otp(mobile):
	# TODO: integrate with message91 or some 3rd party service
	# TODO: wrap this up in celery task
	if settings.ENVIRONMENT != 'prod':
		cache.set(f"{mobile}_{OTP}", '123456', timeout=5 * 60)
		otp_count = cache.get(f"{mobile}_{OTP_COUNT}", 0)
		cache.set(f"{mobile}_{OTP_COUNT}", otp_count + 1, timeout=15 * 60)
		return '123456'

	existing_otp = cache.get(f"{mobile}_{OTP}")
	if existing_otp:
		return existing_otp

	otp_count = cache.get(f"{mobile}_{OTP_COUNT}", 0)
	otp = ''.join(random.choices(string.digits, k=6))
	# call api to send otp
	otp_template = SMS_OTP_TEMPLATE.format(otp=otp)
	status, message = send_sms(mobile, otp_template)
	if not status:
		raise ValueError(f"Could not sent Otp on mobile: {mobile}, Error: {message}")
	high_logger.info(f"Otp successfully sent on mobile no {mobile}")
	cache.set(f"{mobile}_{OTP_COUNT}", otp_count + 1, timeout=15 * 60)
	cache.set(f"{mobile}_{OTP}", otp, timeout=5 * 60)


def verify_otp(mobile, otp):
	# TODO: integrate with message91 or some 3rd party service
	r_otp = cache.get(f"{mobile}_{OTP}")
	if r_otp == otp:
		cache.delete(f"{mobile}_{OTP}")
		return True
	else:
		return False
