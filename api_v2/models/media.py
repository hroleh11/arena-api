import uuid
from pathlib import Path

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.conf import settings
from polymorphic.models import PolymorphicModel
from storages.backends.s3boto3 import S3Boto3Storage

from api_v2.storages import ImageDevStorage, VideoDevStorage, AudioDevStorage, VideoOptimizedStorage


def news_image_name(instance, filename):
    ext = filename.split('.')[-1]
    return f'{instance.global_id}/{instance.global_id}.{ext}'


def video_image_name(instance, filename):
    ext = filename.split('.')[-1]
    try:
        media_global_id = instance.global_id
    except:
        media_global_id = 'unknown'
    return f'{media_global_id}/thumbs-{media_global_id}-00002.{ext}'


def audio_image_name(instance, filename):
    ext = filename.split('.')[-1]
    try:
        media_global_id = instance.global_id
    except:
        media_global_id = 'unknown'
    return f'audios/{media_global_id}/thumbs-{media_global_id}-00001.{ext}'


def video_content_name(instance, filename):
    ext = filename.split('.')[-1]
    try:
        media_global_id = instance.global_id
    except:
        media_global_id = 'unknown'
    return f'{media_global_id}.{ext}'


def audio_content_name(instance, filename):
    ext = filename.split('.')[-1]
    try:
        media_global_id = instance.global_id
    except:
        media_global_id = 'unknown'
    return f'{media_global_id}.{ext}'


class MediaBase(PolymorphicModel):
    class Meta:
        abstract = True

    global_id = models.UUIDField(default=uuid.uuid4, db_index=True)

    is_main = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f'Media: {self.id}'


class MediaImage(MediaBase):
    media_file = models.ImageField(
        upload_to=news_image_name,
        storage=ImageDevStorage(),
        null=True, blank=True
    )
    link = models.URLField(max_length=300, default=None, null=True, blank=True)
    width = models.IntegerField(default=0, null=True)
    height = models.IntegerField(default=0, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='images')

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    @property
    def thumbnail_type(self) -> str:
        return Path(self.media_file.name).suffix[1:].lower()

    @property
    def thumbnail_url(self):
        return f'https://{settings.CDN_DOMAIN_NAME}/{self.media_file}'


class MediaFile(MediaBase):
    class Meta:
        abstract = True

    # For video and audio
    content = models.FileField()
    thumbnail = models.ImageField()
    duration = models.IntegerField(default=0, null=True)

    @property
    def thumbnail_url(self):
        return f'https://{settings.CDN_AUDIOVIDEO_DOMAIN_NAME}/{self.thumbnail}'

    @property
    def type_of_content(self) -> str:
        if self.content:
            return Path(self.content.name).suffix[1:].lower()
        return ''

    @property
    def content_url(self):
        return f'https://{settings.CDN_AUDIOVIDEO_DOMAIN_NAME}/{self.content}'

    @property
    def thumbnail_type(self) -> str:
        return Path(self.thumbnail.name).suffix[1:].lower()

    def get_presigned_url(self, file_ext='', field_name='content', expires_in=3600):
        """
        Generates a presigned URL for the file field.

        :param file_ext: The ext of the file.
        :param field_name: The name of the file field ('content' or 'thumbnail').
        :param expires_in: Expiration time in seconds (default: 3600).
        :return: A presigned URL for uploading to S3.
        """
        # Get the file field
        file_field = getattr(self, field_name, None)
        if not file_field:
            raise ValueError(f"No such field '{field_name}' on this model.")

        # Ensure the field has storage defined
        if not isinstance(file_field.storage, S3Boto3Storage):
            raise ValueError(f"The storage for field '{field_name}' is not S3Boto3Storage.")

        # Extract bucket name, S3 client, and file key
        storage = file_field.storage
        bucket_name = storage.bucket_name
        s3_client = storage.connection.meta.client
        key = file_field.field.generate_filename(self, file_ext)  # Auto-generate the file key based on upload_to

        # Generate presigned URL
        params = {'Bucket': bucket_name, 'Key': key}
        return s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params=params,
            ExpiresIn=expires_in
        )

    # Universal save method
    def save(self, *args, **kwargs):
        thumbnail_file_ext = getattr(self, '_thumbnail_file_ext', 'jpg')

        # Set default thumbnail name if not already set
        if not self.thumbnail or hasattr(self, '_thumbnail_file_ext'):
            self.thumbnail.name = self.generate_thumbnail_name(thumbnail_file_ext)

        # Set default content name if not already set
        if not self.content:
            file_ext = self.default_content_extension
            self.content.name = self.content_path(file_ext)
            print(self.content.name)

        # Clean up temporary attributes
        if hasattr(self, '_thumbnail_file_ext'):
            del self._thumbnail_file_ext

        super().save(*args, **kwargs)

    # Abstract methods to be implemented in subclasses
    def generate_thumbnail_name(self, file_ext):
        raise NotImplementedError("Subclasses must implement this method.")

    @property
    def default_content_extension(self):
        raise NotImplementedError("Subclasses must define a default content extension.")

    def content_path(self, file_ext):
        raise NotImplementedError("Subclasses must implement this method.")


class MediaVideo(MediaFile):
    thumbnail = models.ImageField(
        upload_to=video_image_name,
        storage=VideoOptimizedStorage()
    )
    content = models.FileField(
        upload_to=video_content_name,
        storage=VideoDevStorage()
    )
    width = models.IntegerField(default=0, null=True)
    height = models.IntegerField(default=0, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='videos')

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def content_path(self, file_ext):
        return f'{self.global_id}/{video_content_name(self, file_ext)}'

    def generate_thumbnail_name(self, file_ext):
        return video_image_name(self, file_ext)

    @property
    def default_content_extension(self):
        return 'mp4'


class MediaAudio(MediaFile):
    thumbnail = models.ImageField(
        upload_to=audio_image_name,
        storage=AudioDevStorage()
    )
    content = models.FileField(
        upload_to=audio_content_name,
        storage=AudioDevStorage()
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='audios')

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def content_path(self, file_ext):
        return f'audios/{self.global_id}/{audio_content_name(self, file_ext)}'

    def generate_thumbnail_name(self, file_ext):
        return audio_image_name(self, file_ext)

    @property
    def default_content_extension(self):
        return 'mp3'


__all__ = [
    'MediaBase',
    'MediaImage',
    'MediaFile',
    'MediaVideo',
    'MediaAudio',
]
