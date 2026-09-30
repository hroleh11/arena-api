from api.models import CreatorSocialAssociation
from rest_framework import serializers


class CreatorSocialAssociationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreatorSocialAssociation
        fields = ('id', 'provider', 'username', 'is_submitted')
        read_only_fields = ('id', 'is_submitted')

    @staticmethod
    def validate_username(username):
        if username and username[0] == '@':
            username = username[1:]
        return username

    def validate(self, attrs):
        profile = self.context['request'].user.profile
        if profile.creator_socials.exists():
            raise serializers.ValidationError({'provider': 'You should disconnect this social first'})
        return attrs
