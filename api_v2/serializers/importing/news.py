from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from rest_framework import serializers

from api_v2.models import PublisherNews, MediaImage, UserNews, MediaAudio, MediaVideo, Comments, CuratorNews


class ImportPublisherNewsSerializer(serializers.ModelSerializer):
    media_id = serializers.CharField(required=False, allow_null=True)
    thumbnail_url = serializers.URLField(required=False, allow_null=True)

    class Meta:
        model = PublisherNews
        fields = [
            'global_id', 'category', 'profile',
            'title',  'link', 'published', 'status',
            'external_link', 'web_external_link',
            'created_at', 'updated_at',
            'events_counter',

            'media_id', 'thumbnail_url',
        ]

    def create(self, validated_data):
        media_id = validated_data.pop('media_id', {})
        thumbnail_url = validated_data.pop('thumbnail_url', {})

        with transaction.atomic():
            publisher_news = super().create(validated_data)

            if publisher_news:
                media, _ = MediaImage.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(PublisherNews),
                    object_id=publisher_news.id,
                    is_main=True,
                    global_id=media_id,
                    link=thumbnail_url
                )

        return publisher_news

    def update(self, instance, validated_data):
        media_id = validated_data.pop('media_id', {})
        thumbnail_url = validated_data.pop('thumbnail_url', {})

        with transaction.atomic():
            publisher_news = super().update(instance, validated_data)
            if publisher_news:
                media, _ = MediaImage.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(PublisherNews),
                    object_id=publisher_news.id,
                    is_main=True,
                    global_id=media_id,
                    defaults={
                        'link': thumbnail_url
                    }
                )

        return publisher_news


class ImportUserNewsSerializer(serializers.ModelSerializer):
    media_id = serializers.CharField(required=False, allow_null=True)
    thumbnail_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    content_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    content_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    content_duration = serializers.IntegerField(required=False, default=0)
    content_width = serializers.IntegerField(required=False, default=0)
    content_height = serializers.IntegerField(required=False, default=0)

    response_to = serializers.DictField(required=False, default=None, allow_null=True)

    class Meta:
        model = UserNews
        fields = [
            'global_id', 'category', 'profile',
            'title', 'published', 'status',
            'external_link', 'web_external_link',
            'created_at', 'updated_at',
            'events_counter', 'lineup_global_id',
            'response_to',

            'media_id', 'thumbnail_url', 'content_type',
            'content_url', 'content_duration', 'content_width', 'content_height'
        ]

    def save(self, **kwargs):
        validated_data = self.validated_data
        media_id = validated_data.pop('media_id', None)
        thumbnail_url = validated_data.pop('thumbnail_url', None)
        content_type = validated_data.pop('content_type', None)
        content_url = validated_data.pop('content_url', None)
        content_duration = validated_data.pop('content_duration', 0)
        content_width = validated_data.pop('content_width', 0)
        content_height = validated_data.pop('content_height', 0)

        response_to = validated_data.pop('response_to', None)

        with transaction.atomic():
            user_news = super().save()

            if user_news:
                if content_type in ['mp4', 'MP4']:
                    media, _ = MediaVideo.objects.update_or_create(
                        global_id=media_id,
                        thumbnail=thumbnail_url,
                        content_type=ContentType.objects.get_for_model(UserNews),
                        object_id=user_news.id,
                        is_main=True,
                        content=content_url,
                        width=content_width,
                        height=content_height,
                        duration=content_duration,
                    )

                elif content_type in ['mp3', 'MP3']:
                    media, _ = MediaAudio.objects.update_or_create(
                        global_id=media_id,
                        thumbnail=thumbnail_url,
                        content_type=ContentType.objects.get_for_model(UserNews),
                        object_id=user_news.id,
                        is_main=True,
                        content=content_url,
                        duration=content_duration,
                    )

                if response_to:
                    profile = self.context['profile']
                    comment = self.context.get('comment')
                    response_to_global_id = response_to.get('global_id')
                    if response_to.get('feed_type') != 3:
                        news_obj = PublisherNews.objects.filter(global_id=response_to_global_id).first()
                        if news_obj:
                            response_to_news = news_obj

                        news_obj = UserNews.objects.filter(global_id=response_to_global_id).first()
                        if news_obj:
                            response_to_news = news_obj

                        news_obj = CuratorNews.objects.filter(global_id=response_to_global_id).first()
                        if news_obj:
                            response_to_news = news_obj

                        content_type = ContentType.objects.get_for_model(response_to_news)
                        if comment:
                            Comments.objects.update_or_create(
                                global_id=comment.get('global_id'),
                                defaults={
                                    'text': '',
                                    'content_type': content_type,
                                    'object_id': response_to_news.id,
                                    'user_news': user_news,
                                    'profile': profile,
                                }
                            )
        return user_news
