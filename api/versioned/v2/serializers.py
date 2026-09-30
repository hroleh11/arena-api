from rest_framework import serializers

from api.serializers import (
    ProfileSerializer, ExternalProfileSerializer,
    MyColumnNewsSerializer
)


class ProfileV2Serializer(ProfileSerializer):
    class Meta(ProfileSerializer.Meta):
        fields = (
            'id', 'global_id', 'name', 'username', 'email', 'profile_photo',
            'profile_photo_svg', 'is_source', 'website', 'bio', 'phone', 'is_approved',
            'gender', 'personal_link', 'post_counter', 'followers_counter', 'following_counter',
            'birthday_date', 'timezone', 'is_creator', 'have_access_to_vylo_props', 'dfs_pre_auth_completed', 
            'creator_cash'
        )


class ExternalProfileV2Serializer(ExternalProfileSerializer):
    is_blocked_by_me = serializers.SerializerMethodField(read_only=True)

    class Meta(ProfileSerializer.Meta):
        fields = (
            'id', 'global_id', 'name', 'username', 'email', 'profile_photo',
            'profile_photo_svg', 'is_source', 'website', 'bio', 'phone', 'is_approved',
            'gender', 'personal_link', 'post_counter', 'followers_counter', 'following_counter',
            'birthday_date', 'im_following', 'is_creator', 'is_blocked_by_me'
        )

    def get_is_blocked_by_me(self, profile):
        request = self.context.get('request')
        if request is None:
            return False
        return request.user.profile.i_block_users.filter(blocked_profile__id=profile.id).exists()


def response2comment_counter(comments, responses, response_level: int, max_response_level=2):
    count = responses.count() + comments.count()
    if response_level >= max_response_level:
        return count

    response_level += 1

    for comment in comments:
        count += response2comment_counter(
            comment.comments.all(),
            comment.responses.all(),
            response_level, max_response_level)
    for response in responses:
        count += response2comment_counter(
            response.responses.all(),
            response.comments.all(),
            response_level, max_response_level)

    return count


class MyColumnNewsV2Serializer(MyColumnNewsSerializer):
    response_level = serializers.SerializerMethodField()
    response_counter = serializers.SerializerMethodField()

    class Meta(MyColumnNewsSerializer.Meta):
        fields = (
            'id', 'feed_type', 'global_id', 'title', 'response_level',
            'is_user_news', 'status',
            'category_id', 'category_name',
            'publisher_id', 'publisher_name', 'publisher_username', 'publisher_image', 'publisher_is_approved',
            'link', 'published',
            'response_counter', 'responses_list',
            'response_to', 'origin_global_id',
            'thumbnail_type', 'thumbnail_url',
            'content_type', 'content_url', 'content_duration', 'content_width', 'content_height', 'lineup_global_id',
            'created_at', 'updated_at', 'external_link', 'web_external_link', 'share', 'events_counter',
        )

    @staticmethod
    def get_response_level(obj):
        return 0

    def get_response_counter(self, obj):
        max_response_level = 2
        return response2comment_counter(
            obj.comments.all(),
            obj.responses.all(),
            1,
            max_response_level
        )
