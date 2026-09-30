from rest_framework import serializers
from django.contrib.auth.models import User

from api.models import (
    ColumnNews, NewsReport, Profile,
    ReportedProfiles, BlockedProfiles, MediaLinks, ShareIntroEvents,
    CreatorSocialAssociation, Comments
)
from api.serializers import publishers, categories


class MediaLinksExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaLinks
        fields = ('global_id', 'content_url', 'content_type', 'thumbnail_url', 'origin',
                  'duration', 'width', 'height')


class ColumnNewsExportSerializer(serializers.ModelSerializer):
    publisher = publishers.PublishersSerializer()
    main_media = MediaLinksExportSerializer(read_only=True)
    category = categories.CategoriesSerializer(allow_null=True)

    class Meta:
        model = ColumnNews
        fields = ('global_id', 'category', 'publisher', 'main_media', 'response_type',
                  'title', 'link', 'author', 'published', 'response_to', 'response_chain',
                  'lineup_global_id', 'lineup_data')


class ColumnNewsReportExport(serializers.ModelSerializer):
    profile_id = serializers.UUIDField(source='profile.global_id')

    class Meta:
        model = NewsReport
        fields = ('global_id', 'status', 'profile_id', 'news_global_id')


class UserExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'is_active', 'date_joined']


class ProfileExportSerializer(serializers.ModelSerializer):
    user = UserExportSerializer()
    profile_photo = serializers.ImageField(use_url=False)

    class Meta:
        model = Profile
        fields = ['global_id', 'user', 'profile_photo',
                  'name', 'website', 'bio',
                  'phone', 'gender', 'timezone',
                  'is_source', 'is_approved', 'account_rate', 'signup_code', 'creator_cash']


class ReportedProfilesExportSerializer(serializers.ModelSerializer):
    reporter_profile = serializers.UUIDField(
        source='reporter_profile.global_id')
    reported_profile = serializers.UUIDField(
        source='reported_profile.global_id')

    class Meta:
        model = ReportedProfiles
        fields = ['reporter_profile', 'reported_profile', 'status']


class BlockedProfilesExportSerializer(serializers.ModelSerializer):
    profile_global_id = serializers.UUIDField(source='profile.global_id')
    blocked_profile_global_id = serializers.UUIDField(
        source='blocked_profile.global_id')

    class Meta:
        model = BlockedProfiles
        fields = ['profile_global_id', 'blocked_profile_global_id']


class ShareIntroSerializer(serializers.ModelSerializer):
    feed_id = serializers.UUIDField(source='news.global_id')
    publisher_id = serializers.UUIDField(source='profile.global_id')

    class Meta:
        model = ShareIntroEvents
        fields = ('global_id', 'provider', 'publisher_id', 'feed_id', 'is_closed')


class CreatorSocialSignalSerializer(serializers.ModelSerializer):
    profile_global_id = serializers.UUIDField(source='profile.global_id')

    class Meta:
        model = CreatorSocialAssociation
        fields = ('global_id', 'profile_link', 'profile_global_id', 'provider', 'is_submitted')


class CommentsExportSerializer(serializers.ModelSerializer):
    profile_global_id = serializers.UUIDField(source='profile.global_id')

    class Meta:
        model = Comments
        fields = (
            'global_id', 'response_to', 'profile_global_id',
            'response_chain', 'comment_type', 'text', 'created_at'
        )
