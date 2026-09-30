from rest_framework import serializers

from api_v2.models import Comments


class CommentSerializer(serializers.ModelSerializer):
    publisher_id = serializers.CharField(source='profile.global_id')
    publisher_name = serializers.CharField(max_length=50, default='', allow_null=True, source='profile.name')
    publisher_username = serializers.CharField(
        max_length=24, source='profile.user.username')
    publisher_image = serializers.CharField(default='', allow_null=True, source='profile.profile_photo')
    publisher_image_svg = serializers.CharField(default='', allow_null=True, source='profile.profile_photo_svg')
    publisher_is_approved = serializers.BooleanField(default=False, source='profile.is_approved')

    response_to_comment = serializers.CharField(source='response_to_comment.global_id', default=None, allow_null=True)
    user_news = serializers.CharField(source='user_news.global_id', default=None, allow_null=True)

    object = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Comments
        fields = [
            'id',
            'global_id',
            'publisher_id', 'publisher_name', 'publisher_username',
            'publisher_image', 'publisher_image_svg', 'publisher_is_approved',
            'text',
            'user_news',
            'object',
            'parent',
            'response_to_comment',
            'lineup_global_id',
            'created_at',
            'updated_at',
        ]

    def get_object(self, instance):
        if instance.object:
            return str(getattr(instance.object, 'global_id', None))
        return None

    def get_parent(self, instance):
        if instance.parent:
            return str(instance.parent.global_id)
        return None
