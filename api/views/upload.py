import boto3
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import ColumnNews, MediaLinks
from api.serializers import upload
from api.permissions import IsNewsOwner


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "duration",
                openapi.IN_QUERY,
                description="audio or video duration",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "width",
                openapi.IN_QUERY,
                description="video frame width",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "height",
                openapi.IN_QUERY,
                description="video frame height",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "file_type",
                openapi.IN_QUERY,
                description="audio or video",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ]
    ),
)
class UploadVideo(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, file_ext):
        file_type = request.GET.get('file_type', 'video')
        duration = request.GET.get('duration')
        width = request.GET.get('width')
        height = request.GET.get('height')
        profile = request.user.profile

        if file_type not in ('video', 'audio'):
            return Response({'file_type': ['File may be only video or audio!']}, status=status.HTTP_400_BAD_REQUEST)

        news = ColumnNews.objects.create(title='', publisher=profile, author='', )
        media = MediaLinks.objects.create(column_news=news,
                                          origin='user upload',
                                          duration=duration,
                                          width=width,
                                          height=height)

        news.main_media = media
        news.save()

        if file_type == 'audio':
            dir_name = f'audios/{media.global_id}'
            file_ext = 'mp3'
            thumbnail_name = f'thumbs-{media.global_id}-00001.png'
        else:
            dir_name = media.global_id
            thumbnail_name = f'{media.global_id}.0000000.jpg'
        file_name = f'{media.global_id}.{file_ext}'

        media.content = f'{dir_name}/{file_name}'
        media.thumbnail = f'{dir_name}/{thumbnail_name}'
        media.save()

        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY)
        params = {'Key': file_name}
        if file_type == 'audio':
            params['Bucket'] = settings.AWS_AUDIO_UPLOAD_BUCKET
        else:
            params['Bucket'] = settings.AWS_VIDEO_UPLOAD_BUCKET
        presigned_url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params=params,
            ExpiresIn=3600)

        return Response({
            'news_record_id': news.id,
            'news_record_global_id': news.global_id,
            'media_record_id': media.id,
            'media_record_global_id': media.global_id,
            'file_name': file_name,
            'presigned_url': presigned_url,
        })


class UpdateCoverView(generics.UpdateAPIView):
    serializer_class = upload.UploadSerializer
    permission_classes = (permissions.IsAuthenticated, IsNewsOwner)
    lookup_field = 'global_id'

    def get_queryset(self):
        pass

    def get_object(self):
        global_id = self.kwargs.get(self.lookup_field)
        return get_object_or_404(ColumnNews, global_id=global_id)
