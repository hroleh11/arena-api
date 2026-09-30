from rest_framework import serializers

from api.models import Comments, ColumnNews, SportEvents


class CommentsSerializer(serializers.ModelSerializer):
    feed_type = serializers.ChoiceField(source='comment_type', choices=Comments.Types.choices)

    class Meta:
        model = Comments
        fields = (
            'id', 'global_id',
            'text', 'feed_type', 'response_to',
            'created_at', 'updated_at'
        )
        extra_kwargs = {
            'global_id': {'read_only': True},
        }

    def validate(self, attrs):
        model = {
            Comments.Types.NEWS: ColumnNews,
            Comments.Types.SPORT: SportEvents,
            Comments.Types.COMMENTS: Comments
        }.get(attrs['comment_type'])
        try:
            content_object = model.objects.get(global_id=attrs['response_to'])
        except model.DoesNotExist:
            raise serializers.ValidationError('Invalid response_to')

        attrs['content_object'] = content_object
        return attrs


class CommentsSerializerUpdate(serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = (
            'id', 'global_id', 'text', 'created_at', 'updated_at'
        )
        extra_kwargs = {
            'global_id': {'read_only': True},
        }


__all__ = ['CommentsSerializer', 'CommentsSerializerUpdate']