from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.utils import aware_utcnow, datetime_to_epoch, make_utc, datetime_from_epoch


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def token_refresh(request):
    refresh_token = request.data.get("refresh_token")
    if not refresh_token:
        return Response(data={
            'message': {
                'error': ['missing refresh token']
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    is_blacklisted = True if cache.get(refresh_token) else False
    if is_blacklisted:
        return Response(data={
            'message': {
                'error': ['invalid refresh token']
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh = RefreshToken(refresh_token)
    except TokenError as te:
        return Response(data={
            'message': {
                'error': [str(te)]
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    current_epoch = datetime_to_epoch(make_utc(aware_utcnow()))
    refresh_remaining_expiry = refresh.get('exp') - current_epoch
    if refresh_remaining_expiry <= 0:
        return Response(data={
            'message': {
                'error': ['expired refresh token']
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    # generate new_access_token
    new_access_token = str(refresh.access_token)

    if refresh_remaining_expiry < 3600:
        # less than 1 hour remaining in refresh token expiry
        # blacklist and rotate refresh token
        cache.set(refresh_token, 1, timeout=refresh_remaining_expiry)
        refresh.set_jti()
        refresh.set_exp()
        refresh.set_iat()

    return Response(data={
        'access_token': new_access_token,
        'refresh_token': str(refresh)
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def token_invalidate(request):
    refresh_token = request.data.get("refresh_token")
    access_token = request.data.get("access_token")
    if not access_token or not refresh_token:
        return Response(data={
            'message': {
                'error': ['missing refresh/access token']
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # this will raise TokenError if token is expired
        at = AccessToken(access_token)
        # reaching here means token is not yet expired
        # blacklist it with remaining expiry time
        at_timeout = (datetime_from_epoch(at['exp']) - at.current_time).seconds
        cache.set(access_token, 1, timeout=at_timeout)
    except TokenError:
        pass

    try:
        # this will raise TokenError if token is expired
        rt = RefreshToken(refresh_token)
        # reaching here means token is not yet expired
        # blacklist it with remaining expiry time
        rt_timeout = (datetime_from_epoch(rt['exp']) - rt.current_time).seconds
        cache.set(refresh_token, 1, timeout=rt_timeout)
    except TokenError:
        pass

    return Response(data={}, status=status.HTTP_200_OK)
