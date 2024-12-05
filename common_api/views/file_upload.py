import os
from pathlib import Path

from urllib.parse import urljoin
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import status

from common_api.serializers import ImageUploadSerializer

# TODO:
class FileUploadView(APIView):
    def post(self, request):
        ius = ImageUploadSerializer(data=request.data)
        if ius.is_valid(raise_exception=True):
            image = ius.validated_data['image']
            image_folder = Path.joinpath(settings.MEDIA_ROOT, 'profile_image')
            os.makedirs(image_folder, exist_ok=True)
            image_name = f"uid-{request.user.uid}"
            image_path = Path.joinpath(image_folder, image_name)
            with open(image_path, 'wb') as f:
                f.write(image.read())

            image_url = urljoin(settings.BASE_URL, os.path.join(settings.MEDIA_URL, 'profile_image', image_name))
            request.user.image_url = image_url
            request.user.save()
            return Response(data={
                'image_url': image_url
            }, status=status.HTTP_202_ACCEPTED)
