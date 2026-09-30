from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_save
from rest_framework import serializers

from api.models.news import ColumnNews, MediaLinks


class OldMediaLinks(serializers.ModelSerializer):
    # TODO: Temp decision. Delete it after full new migration
    title = serializers.CharField(max_length=100, default='', allow_blank=True, required=False)
    content = serializers.CharField(max_length=500, required=False)
    thumbnail = serializers.CharField(max_length=500, required=False)

    class Meta:
        model = MediaLinks
        fields = (
            'global_id', 'origin', 'title',
            'duration', 'width', 'height',
            'media_type', 'content', 'thumbnail', 'column_news',
            'created_at', 'updated_at'
        )


class GenericRelatedWriteField(serializers.Field):
    def to_internal_value(self, data):
        if data is None:
            return None
        elif data.get('content_type') is None or data.get('object_id') is None:
            return None

        try:
            content_type_id = data.get('content_type')
            object_id = data.get('object_id')

            if not content_type_id or not object_id:
                raise serializers.ValidationError("Both 'content_type' and 'object_id' are required.")

            content_type = ContentType.objects.get(id=content_type_id)
            model_class = content_type.model_class()

            obj = model_class.objects.get(id=object_id)
            return obj
        except (ContentType.DoesNotExist, model_class.DoesNotExist, KeyError, ValueError):
            raise serializers.ValidationError("Invalid content_type or object_id.")

    def to_representation(self, value):
        return None


class OldNewsSerializer(serializers.ModelSerializer):
    # TODO: Temp decision. Delete it after full new migration
    title = serializers.CharField(max_length=300, default='Test title', required=False)
    media = OldMediaLinks()
    content_object = GenericRelatedWriteField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = ColumnNews
        fields = (
            'id', 'global_id',
            'category', 'publisher', 'title', 'published', 'status',
            'link',
            'media',
            'external_link', 'web_external_link',
            'response_to', 'response_type', 'content_object', 'lineup_global_id',

            'created_at', 'updated_at'
        )

    def validate_title(self, value):
        return value

    def create(self, validated_data):
        media_data = validated_data.pop('media', None)

        # News creation
        with transaction.atomic():
            column_news = super().create(validated_data)

            # Handling media
            if media_data:
                media_data['column_news'] = column_news.pk
                media_serializer = OldMediaLinks(data=media_data)
                if media_serializer.is_valid(raise_exception=True):
                    main_media = media_serializer.save()
                    column_news.main_media = main_media
                    column_news.save()

        post_save.send(
            sender=ColumnNews,
            instance=column_news,
            created=True
        )

        return column_news

    def update(self, instance, validated_data):
        media_data = validated_data.pop('media', None)
        
        # Store old lineup_global_id to check if it changed
        old_lineup_global_id = instance.lineup_global_id

        # Updating news
        with transaction.atomic():
            if media_data:
                media_instance = MediaLinks.objects.filter(column_news=instance).first()
                # Creation or updating media
                if media_instance:
                    media_data['column_news'] = instance.pk
                    media_serializer = OldMediaLinks(media_instance, data=media_data)
                    if media_serializer.is_valid(raise_exception=True):
                        main_media = media_serializer.save()
                        instance.main_media = main_media
                else:
                    media_data['column_news'] = instance.pk
                    media_serializer = OldMediaLinks(data=media_data)
                    if media_serializer.is_valid(raise_exception=True):
                        main_media = media_serializer.save()
                        instance.main_media = main_media

            column_news = super().update(instance, validated_data)
            
            # Check if lineup_global_id changed and trigger post_save signal
            new_lineup_global_id = column_news.lineup_global_id
            if old_lineup_global_id != new_lineup_global_id:
                print(f"Lineup global_id changed from {old_lineup_global_id} to {new_lineup_global_id}")
                # Send post_save signal to trigger lineup data fetch
                post_save.send(
                    sender=ColumnNews,
                    instance=column_news,
                    created=False,
                    update_fields=['lineup_global_id']
                )

        return column_news
