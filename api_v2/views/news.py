import time
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, generics, mixins
from rest_framework.response import Response
from rest_framework.views import APIView

from api_v2.models import UserNews, MediaAudio, MediaVideo
from api_v2.permissions import IsNewsOwner
from api_v2.serializers.news import MediaParamsSerializer, UploadUserNewsResponseSerializer, UserNewsUpdateSerializer


class V2UploadUserNews(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    param_serializer = MediaParamsSerializer

    @swagger_auto_schema(
        query_serializer=MediaParamsSerializer, responses={200: UploadUserNewsResponseSerializer})
    def get(self, request, *args, **kwargs):
        serializer = self.param_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        file_type = validated_data.get('file_type', 'video')
        duration = validated_data.get('duration')
        width = validated_data.get('width')
        height = validated_data.get('height')
        thumbnail_file_ext = validated_data.get('thumbnail_file_ext')
        lineup_global_id = validated_data.get('lineup_global_id')

        if file_type not in ('video', 'audio'):
            return Response({'file_type': ['File may be only video or audio!']}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            news = UserNews.objects.create(title='', profile=request.user.profile, lineup_global_id=lineup_global_id)

            if file_type == 'audio':
                media, _ = MediaAudio.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(UserNews),
                    object_id=news.id,
                    is_main=True,
                    duration=duration,
                )
                file_ext = 'mp3'
            else:
                media, _ = MediaVideo.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(UserNews),
                    object_id=news.id,
                    is_main=True,
                    width=width,
                    height=height,
                    duration=duration,
                )
                file_ext = 'mp4'
            media._thumbnail_file_ext = thumbnail_file_ext
            media.save()

        content_file_name = f'{media.global_id}.{file_ext.lower()}'

        return Response({
            'news_record_id': news.id,
            'news_record_global_id': news.global_id,
            'media_record_id': media.id,
            'media_record_global_id': media.global_id,
            'content_file_name': content_file_name,
            'content_presigned_url': media.get_presigned_url(file_ext),
            'thumbnail_presigned_url': media.get_presigned_url(thumbnail_file_ext, 'thumbnail'),
            'lineup_global_id': lineup_global_id,
        })


class UserNewsUpdate(mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsNewsOwner]
    serializer_class = UserNewsUpdateSerializer
    lookup_field = "global_id"
    queryset = UserNews.objects.all().exclude(status__in=[UserNews.Statuses.DELETED])
    http_method_names = ['put', 'delete']

    def get_queryset(self):
        if self.request.method == 'DELETED':
            exclude_status = [UserNews.Statuses.DELETED, UserNews.Statuses.DRAFT]
            queryset = UserNews.objects.all().exclude(status__in=exclude_status)
        else:
            queryset = super().get_queryset()
        return queryset

    def put(self, request, *args, **kwargs):   
        response = self.update(request, *args, **kwargs)
        time.sleep(8)
        return response

    def perform_update(self, serializer):
        serializer.save(profile=self.request.user.profile)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.status = UserNews.Statuses.DELETED
        instance.save()
