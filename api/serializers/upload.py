import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from rest_framework import serializers

from api.models import ColumnNews


class UploadSerializer(serializers.ModelSerializer):
    cover_ext = serializers.CharField(write_only=True)
    presigned_url = serializers.URLField(read_only=True)
    news_record_id = serializers.CharField(source='id', read_only=True)
    news_record_global_id = serializers.CharField(source='global_id', read_only=True)
    media_record_id = serializers.CharField(source='main_media.id', read_only=True)
    media_record_global_id = serializers.CharField(source='main_media.global_id', read_only=True)

    class Meta:
        model = ColumnNews
        fields = (
            'cover_ext', 'presigned_url', 'news_record_id',
            'news_record_global_id', 'media_record_id', 'media_record_global_id'
        )
        read_only_fields = (
            'presigned_url', 'news_record_id',
            'news_record_global_id', 'media_record_id', 'media_record_global_id'
        )

    @staticmethod
    def validate_cover_ext(cover_ext):
        if cover_ext not in ('jpg', 'jpeg', 'png'):
            raise serializers.ValidationError('This is cover extension is not supported.')
        return cover_ext

    def update(self, instance, validated_data):
        media = instance.main_media

        cover_ext = validated_data.get('cover_ext')

        file_name, extension = media.content.__str__().split('/')[-1].split('.')
        cover_name = f'thumbs-{file_name}-00002.{cover_ext}'

        params = dict()
        if cover_ext == 'mp3':
            params['Key'] = f'audios/{file_name}/{cover_name}'
            params['Bucket'] = settings.AWS_AUDIO_UPLOAD_BUCKET_OPTIMIZED
        else:
            params['Key'] = f'{file_name}/{cover_name}'
            params['Bucket'] = settings.AWS_VIDEO_UPLOAD_BUCKET_OPTIMIZED
        media.thumbnail = params.get('Key')
        media.save()

        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY)

        try:
            s3.delete_object(**params)
        except ClientError:
            pass

        presigned_url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params=params,
            ExpiresIn=3600)
        if instance.status not in (ColumnNews.Statuses.DRAFT, ColumnNews.Statuses.PUBLISHED):
            instance.status = ColumnNews.Statuses.PUBLISHED
            instance.save()
        return {
            'news_record_id': self.instance.id,
            'news_record_global_id': self.instance.global_id,
            'media_record_id': media.id,
            'file_name': cover_name,
            'presigned_url': presigned_url,
        }
