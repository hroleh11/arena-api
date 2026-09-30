from rest_framework import serializers

from api.models import Profile


class PublishersSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    im_following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'global_id', 'username', 'name',
                  'is_source', 'is_approved',
                  'profile_photo', 'profile_photo_svg',
                  'profile_photo_small_thumb', 'profile_photo_big_thumb',
                  'im_following']

    def get_im_following(self, profile):
        request = self.context.get('request')
        if request is None:
            return False
        return request.user.profile.publishers_subscription.filter(id=profile.id).exists()


# Just for naming and future enhancement
class FollowingSerializer(PublishersSerializer):
    pass


class FollowersSerializer(PublishersSerializer):
    pass


class PublishersV2Serializer(PublishersSerializer):
    def get_im_following(self, publisher):
        profile = self.context.get('profile')
        if profile is None:
            return False
        return profile.publishers_subscription.filter(id=publisher.id).exists()
