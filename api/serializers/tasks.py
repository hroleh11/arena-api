from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction

from api.models import (
    ColumnNews, Profile, Categories, MediaLinks,
    ShareIntroEvents, SportEvents, CreatorSocialAssociation,
    AutoFollow
)
from api.validators import validate_username, validate_email

User = get_user_model()


class ColumnNewsTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColumnNews
        fields = (
            'global_id', 'category', 'publisher', 'title',
            'link', 'published', 'status',
            'response_type', 'response_to',
            'external_link', 'web_external_link',
            'lineup_global_id', 'lineup_data'
        )
        extra_kwargs = {
            'title': {'required': False, 'allow_null': True, 'allow_blank': True},
        }


class UserImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'is_active']

    def validate_username(self, username):
        return validate_username(username, self.instance)

    def validate_email(self, email):
        return validate_email(email, self.instance)


class ProfileImportSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.CharField(source='user.email')
    is_active = serializers.BooleanField(source='user.is_active')
    is_elite_creator = serializers.BooleanField(source='is_creator')
    profile_photo = serializers.CharField(allow_null=True)
    profile_photo_svg = serializers.CharField(allow_null=True)

    class Meta:
        model = Profile
        fields = (
            'global_id', 'username', 'email',
            'profile_photo', 'profile_photo_svg',
            'name', 'website', 'bio', 'phone',
            'gender', 'is_source', 'is_approved', 'is_active',
            'is_elite_creator', 'account_rate', 'signup_code',
            'have_access_to_vylo_props', 'dfs_pre_auth_completed', 
            'creator_cash'
        )
        extra_kwargs = {
            'signup_code': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

    def update(self, instance, validated_data):
        instance._is_external = True
        
        user_data = validated_data.pop('user', {})
        serializer = UserImportSerializer(instance.user, data=user_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        
        instance.save()
        
        return instance

    def create(self, validated_data):
        print(validated_data)

        serializer = UserImportSerializer(data=validated_data.pop('user', {}))
        serializer.is_valid(raise_exception=True)

        user = User(**serializer.data)
        user._profile = validated_data

        if validated_data.get('is_creator'):
            password = Profile.generate_password()
            user._password = password
            user.set_password(password)

        user.save()
        return user.profile


def get_object(save):
    def wrapper(self, **kwargs):
        validated_data = self.validated_data
        try:
            validated_data['parent'] = Categories.objects.get(global_id=validated_data.pop('parent_global_id', None))
        except Categories.DoesNotExist:
            validated_data['parent'] = None
        instance = save(self, **kwargs)
        return instance

    return wrapper


class CategoryImportSerializer(serializers.ModelSerializer):
    parent_global_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Categories
        fields = ('id', 'name', 'global_id', 'is_active', 'order', 'parent_global_id', 'category_type', 'code')

    def save(self, **kwargs):
        validated_data = self.validated_data
        parent_global_id = validated_data.pop('parent_global_id', None)
        
        if parent_global_id:
            try:
                parent_category = Categories.objects.get(global_id=parent_global_id)
                validated_data['parent'] = parent_category
            except Categories.DoesNotExist:
                validated_data['parent'] = None
        else:
            validated_data['parent'] = None
            
        return super().save(**kwargs)


class MediaLinksImportSerializer(serializers.ModelSerializer):
    media_id = serializers.UUIDField(source='global_id')
    thumbnail = serializers.CharField(required=False)
    content = serializers.CharField(required=False)
    content_duration = serializers.IntegerField(source='duration', allow_null=True)
    content_width = serializers.IntegerField(source='width', allow_null=True)
    content_height = serializers.IntegerField(source='height', allow_null=True)

    class Meta:
        model = MediaLinks
        fields = (
            'media_id', 'content_duration', 'content_width', 'content_height',
            'thumbnail', 'content', 'column_news'
        )


class ShareIntroSerializer(serializers.ModelSerializer):
    profile_global_id = serializers.UUIDField(source='profile.global_id')
    news_global_id = serializers.UUIDField(source='news.global_id')

    class Meta:
        model = ShareIntroEvents
        fields = ('global_id', 'profile_global_id', 'news_global_id', 'provider', 'is_closed')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs['profile'] = Profile.objects.get(global_id=attrs['profile']['global_id'])
        attrs['news'] = ColumnNews.objects.get(global_id=attrs['news']['global_id'])
        return attrs


class SportEventsSerializer(serializers.ModelSerializer):
    category_id = serializers.UUIDField(source='category.global_id')
    home_team_image = serializers.CharField(allow_null=True)
    away_team_image = serializers.CharField(allow_null=True)
    market = serializers.JSONField(allow_null=True)

    class Meta:
        model = SportEvents
        fields = ('global_id', 'uid', 'category_id', 'category_abbr',
                  'market', 'commence_time', 'is_completed',
                  'home_team_name', 'home_team_image', 'home_score',
                  'away_team_name', 'away_team_image', 'away_score')

    def save(self, **kwargs):
        validated_data = self.validated_data
        category = validated_data.pop('category', {})
        try:
            validated_data['category'] = Categories.objects.get(global_id=category.get('global_id'))
        except Categories.DoesNotExist:
            validated_data['category'] = None
        instance = super().save(**kwargs)
        return instance


class CreatorSocialTasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreatorSocialAssociation
        fields = ('global_id', 'profile', 'username', 'provider', 'is_submitted')


class AutoFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoFollow
        fields = ('global_id', 'profile', 'sort_order', 'description')
