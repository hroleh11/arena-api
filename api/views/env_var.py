from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from django.conf import settings


class EnvVar(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        resp = {
            'Android': {'app_version': settings.ANDROID_APP_VERSION}
        }
        return Response(resp)
