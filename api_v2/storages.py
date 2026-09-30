from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class ContentDevStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    custom_domain = None


class ImageDevStorage(S3Boto3Storage):
    bucket_name = settings.AWS_NEWS_STORAGE_BUCKET_NAME


class VideoDevStorage(S3Boto3Storage):
    bucket_name = settings.AWS_VIDEO_UPLOAD_BUCKET


class AudioDevStorage(S3Boto3Storage):
    bucket_name = settings.AWS_AUDIO_UPLOAD_BUCKET


class VideoOptimizedStorage(S3Boto3Storage):
    bucket_name = settings.AWS_VIDEO_UPLOAD_BUCKET_OPTIMIZED
