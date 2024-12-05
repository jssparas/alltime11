import logging

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework.request import Request
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
LOGGER = logging.getLogger("api")


class AllTimeAuthentication(JWTAuthentication):
    def authenticate(self, request: Request):
        LOGGER.info("authentication request from middleware")
        if request.META.get('HTTP_DEMO_USER') and settings.DEBUG:
            return User.objects.get(pk=request.META.get('HTTP_DEMO_USER')), None

        auth_values = super().authenticate(request)
        if auth_values is None:
            return None

        user, token = auth_values

        if cache.get(token):
            raise AuthenticationFailed(
                {
                    "detail": _("invalid or expired token provided"),
                    "code": "invalid/expired token",
                }
            )

        if not user.is_active or user.is_blocked:
            raise AuthenticationFailed(
                {
                    "detail": _("The user is either deleted or blocked in the system"),
                    "code": "deleted_or_blocked",
                }
            )
        return user, token
