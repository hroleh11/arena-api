from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from rest_framework import serializers

from api.models import Categories
from api_v2.models import CuratorNews, MediaVideo, MediaImage


class MediaImageImportSerializer(serializers.ModelSerializer):
    media_file_name = serializers.CharField()

    class Meta:
        model = MediaImage
        fields = [
            'global_id',
            'width', 'height', 'media_file_name',
            'created_at', 'updated_at'
        ]


class MediaVideoImportSerializer(serializers.ModelSerializer):
    content_name = serializers.CharField()
    thumbnail_name = serializers.CharField()

    class Meta:
        model = MediaVideo
        fields = [
            'global_id',
            'width', 'height', 'duration',
            'content_name', 'thumbnail_name',
            'created_at', 'updated_at'
        ]


class MainMediaImportField(serializers.Serializer):
    """Field for dynamic selection of serializer depending on type."""
    media_type = serializers.ChoiceField(choices=CuratorNews.Types.choices)

    def to_representation(self, value):
        """Determines which serializer to use to output data."""
        if value.type == CuratorNews.Types.PHOTO:
            return MediaImageImportSerializer(value.main_image).data
        elif value.type == CuratorNews.Types.VIDEO:
            return MediaVideoImportSerializer(value.main_video).data
        return None

    def to_internal_value(self, data):
        """Processes incoming data."""
        media_type = data.get('media_type')
        if media_type == CuratorNews.Types.PHOTO:
            serializer = MediaImageImportSerializer(data=data)
        elif media_type == CuratorNews.Types.VIDEO:
            serializer = MediaVideoImportSerializer(data=data)
        else:
            raise serializers.ValidationError("Invalid media_type.")

        serializer.is_valid(raise_exception=True)
        return {'media_type': media_type, 'data': serializer.validated_data}


class CuratorNewsImport(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Categories.objects.all(),
        required=True, read_only=False, slug_field='global_id'
    )
    main_media = MainMediaImportField(write_only=True, required=False, allow_null=True)
    profile = serializers.JSONField()

    class Meta:
        model = CuratorNews
        fields = (
            'global_id', 'category', 'profile', 'type',
            'main_media',
            'title', 'status', 'external_link', 'web_external_link',
            'main_prop', 'props', 'lineup_global_id',
            'created_at', 'updated_at'
        )

    def save(self, **kwargs):
        validated_data = self.validated_data
        main_media = validated_data.pop('main_media', {})

        with transaction.atomic():
            curator_news = super().save(**kwargs)
            if main_media:
                media_type = main_media.pop('media_type')
                media_data = main_media.get('data', {})

                if media_type == CuratorNews.Types.PHOTO:
                    media_file_name = media_data.pop('media_file_name')
                    MediaImage.objects.create(
                        content_type=ContentType.objects.get_for_model(CuratorNews),
                        object_id=curator_news.id,
                        is_main=True,
                        media_file=media_file_name,
                        **media_data
                    )
                elif media_type == CuratorNews.Types.VIDEO:
                    content_name = media_data.pop('content_name')
                    thumbnail_name = media_data.pop('thumbnail_name')
                    MediaVideo.objects.create(
                        content_type=ContentType.objects.get_for_model(CuratorNews),
                        object_id=curator_news.id,
                        is_main=True,
                        content=f'{media_data["global_id"]}/{content_name}',
                        thumbnail=thumbnail_name,
                        **media_data
                    )

        return curator_news

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.images.all().delete()
            instance.videos.all().delete()
            return super().update(instance, validated_data)
