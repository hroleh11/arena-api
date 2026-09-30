from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.models import (
    ColumnNews, NewsReport, Categories,
    ShareIntroEvents, SportEvents, Comments, MediaLinks
)
from api_v2.models import CuratorNews
from api_v2.models import Comments as CommentsV2
from api_v2.serializers.news import ResponseToFeedSerializer, UserNewsResponseSerializer


class ResponseToUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColumnNews
        fields = ['id', 'global_id']


class NewsUpdateSerializer(serializers.ModelSerializer):
    global_id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(max_length=300)
    feed_type = serializers.IntegerField(source='response_type', required=False)
    category_global_id = serializers.UUIDField(source='category.global_id', required=False, allow_null=True)

    class Meta:
        model = ColumnNews
        fields = ('id', 'category_global_id', 'link', 'feed_type',
                  'title', 'global_id', 'response_to')
        extra_kwargs = {
            'link': {'required': False},
        }

    def validate(self, attrs):
        category_data = attrs.get('category', None)
        if category_data:
            try:
                attrs['category'] = Categories.objects.get(
                    is_active=True, global_id=category_data.pop('global_id', None))
            except Categories.DoesNotExist:
                raise ValidationError("Category global id does not exist")

        response_type = attrs.get('response_type', None)
        response_to = attrs.get('response_to', None)

        if response_to is not None:
            is_style_without_sportbook = bool(response_type is None)
            if is_style_without_sportbook:
                response_type = ColumnNews.ResponseTypes.NEWS.value
                attrs['response_type'] = response_type

            if response_type == ColumnNews.ResponseTypes.NEWS.value:
                try:
                    content_object = ColumnNews.objects.get(global_id=response_to)
                except ColumnNews.DoesNotExist:
                    raise ValidationError({"response_to": "ColumnNews does not exist"})
            elif response_type == ColumnNews.ResponseTypes.SPORT_EVENTS.value:
                try:
                    content_object = SportEvents.objects.get(global_id=response_to)
                except SportEvents.DoesNotExist:
                    raise ValidationError({"response_to": "SportEvent does not exist"})
            elif response_type == ColumnNews.ResponseTypes.COMMENTS.value:
                try:
                    content_object = Comments.objects.get(global_id=response_to)
                except ColumnNews.DoesNotExist:
                    raise ValidationError({"response_to": "Comment does not exist"})
            else:
                raise ValidationError({"response_type": "Invalid response type"})

            attrs['content_object'] = content_object
        else:
            attrs['response_type'] = None
        return super().validate(attrs)

    def update(self, instance, validated_data):
        validated_data['status'] = ColumnNews.Statuses.PUBLISHED
        validated_data['external_link'] = None
        return super().update(instance, validated_data)


class ResponseToSerializer(serializers.ModelSerializer):
    feed_type = serializers.SerializerMethodField()
    is_user_news = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField(
        method_name='get_category_global_id')
    category_name = serializers.SerializerMethodField()
    publisher_id = serializers.UUIDField(source='publisher.global_id')
    publisher_name = serializers.CharField(source='publisher.name')
    publisher_username = serializers.CharField(source='publisher.username')
    publisher_image = serializers.ImageField(source='publisher.profile_photo')
    publisher_image_svg = serializers.FileField(source='publisher.profile_photo_svg', allow_null=True)
    publisher_is_approved = serializers.BooleanField(source='publisher.is_approved')

    thumbnail_url = serializers.URLField(source='main_media.thumbnail_url', allow_null=True)
    content_url = serializers.URLField(source='main_media.content_url', allow_null=True)
    content_type = serializers.CharField(source='main_media.content_type', allow_null=True)

    class Meta:
        model = ColumnNews
        fields = ['id', 'feed_type', 'global_id', 'is_user_news',
                  'category', 'category_name',
                  'publisher_id', 'publisher_name', 'publisher_username',
                  'publisher_image', 'publisher_image_svg',
                  'publisher_is_approved',
                  'thumbnail_url', 'content_url', 'content_type',
                  'title', 'link', 'author', 'published']

    @staticmethod
    def get_feed_type(obj):
        return ColumnNews.ResponseTypes.NEWS.value

    @staticmethod
    def get_title(obj):
        title = obj.title
        if obj.content_object and obj.response_type == ColumnNews.ResponseTypes.NEWS.value:
            title += f' {obj.content_object.publisher.username}: {obj.content_object.title}'
        return title

    @staticmethod
    def get_is_user_news(obj) -> bool:
        return not obj.publisher.is_source

    @staticmethod
    def get_category_global_id(obj):
        if obj.category is None:
            return None
        return str(obj.category.global_id)

    @staticmethod
    def get_category_name(obj):
        if obj.category is None:
            return ''
        return obj.category.name


class CommentToSerializer(serializers.ModelSerializer):
    feed_type = serializers.SerializerMethodField()
    publisher_id = serializers.UUIDField(source='profile.global_id')
    publisher_name = serializers.CharField(source='profile.name')
    publisher_username = serializers.CharField(source='profile.username')
    publisher_image = serializers.ImageField(source='profile.profile_photo')
    publisher_image_svg = serializers.FileField(source='profile.profile_photo_svg', allow_null=True)
    publisher_is_approved = serializers.BooleanField(source='profile.is_approved')

    class Meta:
        model = Comments
        fields = (
            'id', 'global_id', 'feed_type',
            'text', 'publisher_id', 'publisher_name', 'publisher_username',
            'publisher_image', 'publisher_image_svg', 'publisher_is_approved',
            'created_at', 'updated_at')

    @staticmethod
    def get_feed_type(obj):
        return ColumnNews.ResponseTypes.COMMENTS.value


class ResponseToV2CommentsSerializer(serializers.ModelSerializer):
    feed_type = serializers.SerializerMethodField()
    publisher_id = serializers.UUIDField(source='profile.global_id')
    publisher_name = serializers.CharField(source='profile.name')
    publisher_username = serializers.CharField(source='profile.username')
    publisher_image = serializers.ImageField(source='profile.profile_photo')
    publisher_image_svg = serializers.FileField(source='profile.profile_photo_svg', allow_null=True)
    publisher_is_approved = serializers.BooleanField(source='profile.is_approved')

    user_news = UserNewsResponseSerializer(read_only=True, allow_null=True)

    class Meta:
        model = CommentsV2
        fields = (
            'id', 'global_id', 'feed_type',
            'text', 'user_news',
            'publisher_id', 'publisher_name', 'publisher_username',
            'publisher_image', 'publisher_image_svg', 'publisher_is_approved',
            'created_at', 'updated_at'
        )

    @staticmethod
    def get_feed_type(obj):
        return ColumnNews.ResponseTypes.COMMENTS.value


class ResponseToEventSerializer(serializers.ModelSerializer):
    feed_type = serializers.SerializerMethodField()
    odds_type = serializers.IntegerField(source='category.odds_type', allow_null=True)
    home_team_image = serializers.CharField(allow_null=True)
    away_team_image = serializers.CharField(allow_null=True)

    class Meta:
        model = SportEvents
        fields = ('feed_type', 'odds_type', 'global_id', 'commence_time', 'market', 'final_score',
                  'home_team_name', 'home_team_image', 'away_team_name', 'away_team_image')

    @staticmethod
    def get_feed_type(obj):
        return ColumnNews.ResponseTypes.SPORT_EVENTS.value


class MyColumnNewsSerializer(serializers.ModelSerializer):
    feed_type = serializers.SerializerMethodField()
    is_user_news = serializers.BooleanField(default=True)
    category_id = serializers.UUIDField(source='category.global_id', allow_null=True)
    category_name = serializers.CharField(source='category.name', allow_null=True)
    publisher_id = serializers.UUIDField(source='publisher.global_id')
    publisher_name = serializers.CharField(source='publisher.name')
    publisher_username = serializers.CharField(source='publisher.username')
    publisher_image = serializers.ImageField(source='publisher.profile_photo')
    publisher_is_approved = serializers.BooleanField(source='publisher.is_approved')

    thumbnail_url = serializers.URLField(source='main_media.thumbnail_url', allow_null=True)
    thumbnail_type = serializers.CharField(source='main_media.thumbnail_type', allow_null=True)
    content_url = serializers.URLField(source='main_media.content_url', allow_null=True)
    content_type = serializers.CharField(source='main_media.content_type', allow_null=True)
    content_duration = serializers.IntegerField(source='main_media.duration', allow_null=True)
    content_width = serializers.IntegerField(source='main_media.width', allow_null=True)
    content_height = serializers.IntegerField(source='main_media.height', allow_null=True)

    response_counter = serializers.SerializerMethodField()
    responses_list = serializers.SerializerMethodField()

    response_to = serializers.SerializerMethodField()
    origin_global_id = serializers.UUIDField(source='response_to', allow_null=True)

    share = serializers.SerializerMethodField()
    lineup_data = serializers.SerializerMethodField()

    class Meta:
        model = ColumnNews
        fields = [
            'id', 'feed_type', 'global_id', 'is_user_news', 'status',
            'category_id', 'category_name',
            'publisher_id', 'publisher_name', 'publisher_username', 'publisher_image', 'publisher_is_approved',
            'title', 'link', 'published',
            'response_counter', 'responses_list',
            'response_to', 'origin_global_id',
            'thumbnail_type', 'thumbnail_url',
            'content_type', 'content_url', 'content_duration', 'content_width', 'content_height',
            'lineup_global_id', 'lineup_data',
            'created_at', 'updated_at', 'external_link', 'web_external_link', 'share'
        ]

    @staticmethod
    def get_feed_type(obj):

        if (obj.main_media and obj.main_media.media_type == MediaLinks.MediaTypes.VIDEO) and bool(obj.lineup_global_id):
            return 5
        elif bool(obj.lineup_global_id):
            return 4
        else:
            return 1

    @staticmethod
    def get_response_counter(news):
        return news.responses.filter(status=ColumnNews.Statuses.APPROVED).count()

    @staticmethod
    def get_responses_list(news):
        responses = news.responses.filter(status=ColumnNews.Statuses.APPROVED)
        responses_list = [{
            'global_id': r.global_id,
            'publisher_id': r.publisher.global_id,
            'publisher_name': r.publisher.name,
            'publisher_username': r.publisher.username,
            'publisher_image': r.publisher.profile_photo_url,
            'publisher_is_approved': r.publisher.is_approved,
            'thumbnail_type': r.main_media.thumbnail_type,
            'thumbnail_url': r.main_media.thumbnail_url} for r in responses]

        return responses_list

    @staticmethod
    def get_response_to(news):
        origin = news.content_object
        if origin:

            if news.response_type == ColumnNews.ResponseTypes.NEWS:
                if isinstance(origin, ColumnNews):
                    serializer = ResponseToSerializer
                elif isinstance(origin, CuratorNews):
                    serializer = ResponseToFeedSerializer  # TODO: write serializer for curator news
                else:
                    return
            elif news.response_type == ColumnNews.ResponseTypes.COMMENTS:
                serializer = ResponseToV2CommentsSerializer
            elif news.response_type == ColumnNews.ResponseTypes.SPORT_EVENTS:
                serializer = ResponseToEventSerializer
            else:
                return

            return serializer(origin).data

    @staticmethod
    def get_share(news):
        valid_status = [ColumnNews.Statuses.PUBLISHED, ColumnNews.Statuses.APPROVED]
        if (news.main_media and news.main_media.media_type == MediaLinks.MediaTypes.VIDEO) and news.status in valid_status:
            share = {
                'nth_post': ColumnNews.objects.filter(
                    publisher=news.publisher,
                    published__lte=news.published,
                    status__in=valid_status,
                    main_media__media_type=1).count(),
                'to_platform': ShareIntroEvents.objects.filter(news=news).exclude(
                    provider__isnull=True).values_list('provider', flat=True).distinct(),
                'closed': any(ShareIntroEvents.objects.filter(news=news).values_list('is_closed', flat=True))
            }
            return share

    def get_lineup_data(self, news):
        """
        Get lineup data for the news item.
        First check if data is already cached in the model,
        otherwise return None (data will be fetched asynchronously)
        """
        if hasattr(news, 'lineup_data') and news.lineup_data:
            return news.lineup_data
        
        # If lineup_global_id exists but no data yet, trigger async fetch
        if news.lineup_global_id and not news.lineup_data:
            from api.tasks import fetch_lineup_data
            fetch_lineup_data.delay(news.pk, str(news.lineup_global_id))
            
        return None


class ColumnNewsReport(serializers.ModelSerializer):
    class Meta:
        model = NewsReport
        fields = ('id', 'status', 'profile', 'news_global_id')
        extra_kwargs = {
            "profile": {"read_only": True},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        profile = self.context['request'].user.profile

        reports = NewsReport.objects.filter(profile=profile, news_global_id=attrs.get('news_global_id'))
        if not reports:
            attrs['profile'] = profile
            return attrs
        raise ValidationError({'news_global_id': ['A complaint about the news has already been sent!']})

# TODO implement UploadSerializer to generate_presigned_url
# class UploadSerializer(serializers.ModelSerializer):
#     cover_ext = serializers.CharField(write_only=True)
#     presigned_url = serializers.URLField(read_only=True)
#     news_record_id = serializers.CharField(source='id', read_only=True)
#     news_record_global_id = serializers.CharField(source='global_id', read_only=True)
#     media_record_id = serializers.CharField(source='main_media.id', read_only=True)
#     media_record_global_id = serializers.CharField(source='main_media.global_id', read_only=True)
#
#     class Meta:
#         model = CollectedNews
#         fields = (
#             'cover_ext', 'presigned_url', 'news_record_id',
#             'news_record_global_id', 'media_record_id', 'media_record_global_id'
#         )
#         read_only_fields = (
#             'presigned_url', 'news_record_id',
#             'news_record_global_id', 'media_record_id', 'media_record_global_id'
#         )
#
#     @staticmethod
#     def validate_cover_ext(cover_ext):
#         if cover_ext not in ('jpg', 'jpeg', 'png'):
#             raise serializers.ValidationError('This is cover extension is not supported.')
#         return cover_ext
#
#     def update(self, instance, validated_data):
#         media = instance.main_media
#
#         cover_ext = validated_data.get('cover_ext')
#
#         file_name, extension = media.content.__str__().split('/')[-1].split('.')
#         cover_name = f'thumbs-{file_name}-00002.{cover_ext}'
#
#         params = dict()
#         if cover_ext == 'mp3':
#             params['Key'] = f'audios/{file_name}/{cover_name}'
#             params['Bucket'] = settings.AWS_AUDIO_UPLOAD_BUCKET_OPTIMIZED
#         else:
#             params['Key'] = f'{file_name}/{cover_name}'
#             params['Bucket'] = settings.AWS_VIDEO_UPLOAD_BUCKET_OPTIMIZED
#         media.thumbnail = params.get('Key')
#         media.save()
#
#         s3 = client(
#             's3',
#             aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
#             aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY)
#
#         try:
#             s3.delete_object(**params)
#         except ClientError:
#             pass
#
#         presigned_url = s3.generate_presigned_url(
#             ClientMethod='put_object',
#             Params=params,
#             ExpiresIn=3600)
#
#         return {
#             'news_record_id': self.instance.id,
#             'news_record_global_id': self.instance.global_id,
#             'media_record_id': media.id,
#             'file_name': cover_name,
#             'presigned_url': presigned_url,
#         }

__all__ = [
    'ResponseToUpdateSerializer', 'NewsUpdateSerializer',
    'ResponseToSerializer', 'ResponseToEventSerializer',
    'MyColumnNewsSerializer', 'ColumnNewsReport'
]