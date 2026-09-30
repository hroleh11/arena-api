from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.models import Categories, ColumnNews
from api_v2.models import UserNews, Comments, CuratorNews


class MediaParamsSerializer(serializers.Serializer):
    duration = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Audio or video duration in seconds.",
    )
    width = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Video frame width in pixels.",
    )
    height = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Video frame height in pixels.",
    )
    file_type = serializers.ChoiceField(
        choices=["audio", "video"],
        required=True,
        help_text="Type of the file, either 'audio' or 'video'.",
    )
    thumbnail_file_ext = serializers.CharField(
        required=False,
        default='jpg',
        help_text="Thumbnail file extension.",
    )
    lineup_global_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Optional lineup global ID for the news item.",
    )
    @staticmethod
    def validate_thumbnail_file_ext(thumbnail_file_ext):
        if thumbnail_file_ext not in ('jpg', 'jpeg', 'png'):
            raise serializers.ValidationError('This is cover extension is not supported.')
        return thumbnail_file_ext


class UploadUserNewsResponseSerializer(serializers.Serializer):
    news_record_id = serializers.IntegerField(help_text="ID of the news entry in the database.")
    news_record_global_id = serializers.UUIDField(help_text="Global ID of the news item.")
    media_record_id = serializers.IntegerField(help_text="ID of the media file entry in the database.")
    media_record_global_id = serializers.UUIDField(help_text="Global ID of the media item.")
    content_file_name = serializers.CharField(help_text="The name of the file to be downloaded.")
    content_presigned_url = serializers.URLField(help_text="URL to upload the file.")
    thumbnail_presigned_url = serializers.URLField(help_text="URL for uploading cover for media file.")


class UserNewsUpdateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=300)
    category_global_id = serializers.UUIDField(required=False, write_only=True, allow_null=True)
    lineup_global_id = serializers.UUIDField(required=False, allow_null=True, default=None)

    response_to_news_global_id = serializers.UUIDField(required=False, default=None, write_only=True)
    parent_comment_global_id = serializers.UUIDField(required=False, default=None, write_only=True)
    response_to_comment_global_id = serializers.UUIDField(required=False, default=None, write_only=True)

    class Meta:
        model = UserNews
        fields = (
            'id', 'category_global_id', 'title', 'global_id', 'lineup_global_id',
            'response_to_news_global_id', 'parent_comment_global_id', 'response_to_comment_global_id'
        )
        read_only_fields = (
            'id', 'global_id'
        )

    def validate(self, attrs):
        category_global_id = attrs.pop('category_global_id', None)
        response_to_news_global_id = attrs.get('response_to_news_global_id', None)
        parent_comment_global_id = attrs.pop('parent_comment_global_id', None)
        response_to_comment_global_id = attrs.pop('response_to_comment_global_id', None)

        if category_global_id:
            try:
                attrs['category'] = Categories.objects.get(is_active=True, global_id=category_global_id)
            except Categories.DoesNotExist:
                raise serializers.ValidationError("Category global id does not exist")

        if response_to_news_global_id:
            try:
                attrs['news'] = self.Meta.model.objects.get_news_obj(global_id=response_to_news_global_id)
            except ObjectDoesNotExist:
                raise serializers.ValidationError("News with this global id does not exist")

        if parent_comment_global_id:
            try:
                attrs['parent_comment'] = Comments.objects.filter(global_id=parent_comment_global_id).first()
            except ObjectDoesNotExist:
                raise ValidationError("Parent comment with this global id does not exist")

        if response_to_comment_global_id:
            try:
                attrs['response_comment'] = Comments.objects.filter(global_id=response_to_comment_global_id).first()
            except ObjectDoesNotExist:
                raise ValidationError("Comment for response with this global id does not exist")

        return attrs

    def update(self, instance, validated_data):
        with transaction.atomic():
            validated_data['status'] = UserNews.Statuses.PUBLISHED
            validated_data['external_link'] = None

            if validated_data.get('news'):
                profile = self.context['request'].user.profile
                try:
                    Comments.objects.create(
                        text='',
                        object=validated_data['news'],
                        parent=validated_data.get('parent_comment'),
                        user_news=instance,
                        response_to_comment=validated_data.get('response_comment'),
                        profile=profile
                    )
                except IntegrityError:
                    raise serializers.ValidationError("Comment with this news already exists")

            validated_data.pop('response_to_news_global_id', None)
            validated_data.pop('parent_comment', None)
            validated_data.pop('response_comment', None)
            validated_data.pop('news', None)

            return super().update(instance, validated_data)


class UserNewsResponseSerializer(serializers.ModelSerializer):
    feed_type = serializers.SerializerMethodField()
    is_user_news = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField(
        method_name='get_category_global_id')
    category_name = serializers.SerializerMethodField()
    publisher_id = serializers.UUIDField(source='profile.global_id')
    publisher_name = serializers.CharField(source='profile.name')
    publisher_username = serializers.CharField(source='profile.username')
    publisher_image = serializers.ImageField(source='profile.profile_photo')
    publisher_image_svg = serializers.FileField(source='profile.profile_photo_svg', allow_null=True)
    publisher_is_approved = serializers.BooleanField(source='profile.is_approved')

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
                  'title', 'published', 'lineup_global_id']

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
        return not obj.profile.is_source

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


class ResponseToFeedSerializer(serializers.ModelSerializer):
    feed_type = serializers.SerializerMethodField()
    # is_user_news = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField(
        method_name='get_category_global_id')
    category_name = serializers.SerializerMethodField()
    publisher_id = serializers.SerializerMethodField()
    publisher_name = serializers.SerializerMethodField()
    publisher_username = serializers.SerializerMethodField()
    publisher_image = serializers.SerializerMethodField()
    publisher_image_svg = serializers.SerializerMethodField()
    publisher_is_approved = serializers.SerializerMethodField()

    thumbnail_url = serializers.URLField(source='main_media.thumbnail_url', allow_null=True)
    content_url = serializers.URLField(source='main_media.content_url', allow_null=True)
    # content_type = serializers.CharField(source='main_media.content_type', allow_null=True)

    class Meta:
        model = CuratorNews
        fields = [
            'id', 'feed_type', 'global_id',
            'type',
            'category', 'category_name',
            'publisher_id', 'publisher_name', 'publisher_username',
            'publisher_image', 'publisher_image_svg', 'publisher_is_approved',
            'thumbnail_url', 'content_url',
            'title', 'published',
            'main_prop', 'props'
        ]

    def get_publisher_id(self, obj):
        return obj.profile.get('publisher_id') if obj.profile else None

    def get_publisher_name(self, obj):
        return obj.profile.get('publisher_name') if obj.profile else None

    def get_publisher_username(self, obj):
        return obj.profile.get('publisher_username') if obj.profile else None

    def get_publisher_image(self, obj):
        return obj.profile.get('publisher_image') if obj.profile else None

    def get_publisher_image_svg(self, obj):
        return obj.profile.get('publisher_image_svg') if obj.profile else None

    def get_publisher_is_approved(self, obj):
        return obj.profile.get('publisher_is_approved') if obj.profile else None

    @staticmethod
    def get_feed_type(obj):
        return ColumnNews.ResponseTypes.NEWS.value

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
