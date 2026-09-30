from rest_framework import serializers

from api_v2.models import CuratorNews, PublisherNews, UserNews
from api_v2.models.comments import Comments


class V2CommentsSerializer(serializers.ModelSerializer):
    news_global_id = serializers.UUIDField(required=True, write_only=True)
    parent_global_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    response_to_comment = serializers.SlugRelatedField(
        queryset=Comments.objects.all(),
        read_only=False, required=False, slug_field='global_id'
    )
    # user_news = serializers.SlugRelatedField(
    #     queryset=UserNews.objects.all(),
    #     read_only=False, required=False, slug_field='global_id'
    # )
    related_news_global_id = serializers.SerializerMethodField()

    class Meta:
        model = Comments
        fields = (
            'id', 'global_id',
            # 'user_news',
            'text', 'news_global_id', 'parent_global_id', 'response_to_comment',
            'related_news_global_id',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'global_id', 'created_at', 'updated_at')

    def model_get_parent(self, parent_global_id):
        """Validate the parent comment if provided."""
        if not parent_global_id:
            return None

        try:
            parent_comment = Comments.objects.get(global_id=parent_global_id)
        except Comments.DoesNotExist:
            raise serializers.ValidationError('Parent comment with the given global_id does not exist.')

        # Check tree depth using MPTT
        if parent_comment.get_level() >= 1:  # Limiting depth to 1
            raise serializers.ValidationError('Maximum tree depth of 1 level exceeded.')

        return parent_comment

    def model_get_news_global_id(self, news_global_id):
        """Validate the news_global_id and return the specific news object."""
        # First try new architecture models
        for model in [CuratorNews, PublisherNews, UserNews]:
            try:
                return model.objects.get(global_id=news_global_id)
            except model.DoesNotExist:
                continue

        # If not found in new architecture, try old architecture (ColumnNews)
        from api.models import ColumnNews
        try:
            column_news = ColumnNews.objects.get(global_id=news_global_id)
            # Create a mock object that has the same interface as new architecture models
            class MockNewsObject:
                def __init__(self, column_news):
                    self.global_id = column_news.global_id
                    self.id = column_news.id
                    self.title = column_news.title
                    self.published = column_news.published
                    self.publisher = column_news.publisher
                    self.category = column_news.category
                    self.lineup_global_id = column_news.lineup_global_id
                    self.lineup_data = column_news.lineup_data
                    self._column_news = column_news
                    # Add any other attributes that might be needed
                    self.profile = column_news.publisher  # For compatibility
                    
                def __str__(self):
                    return f"MockNewsObject({self.global_id})"
                    
                def __getattr__(self, name):
                    # Fallback to column_news for any missing attributes
                    return getattr(self._column_news, name, None)
                    
            return MockNewsObject(column_news)
        except ColumnNews.DoesNotExist:
            pass

        raise serializers.ValidationError({'news_global_id': 'News with the given global_id does not exist.'})

    def to_internal_value(self, data):
        # Fetch `news_global_id` and `parent_global_id` as internal values
        internal_data = super().to_internal_value(data)

        # Add these explicitly to validated data
        news_global_id = internal_data.get('news_global_id')
        parent_global_id = internal_data.get('parent_global_id')
        
        # Remove these fields from internal_data since they're write_only
        if 'news_global_id' in internal_data:
            del internal_data['news_global_id']
        if 'parent_global_id' in internal_data:
            del internal_data['parent_global_id']

        if news_global_id:
            try:
                internal_data['object'] = self.model_get_news_global_id(news_global_id)
            except serializers.ValidationError as e:
                raise e
        if parent_global_id:
            try:
                internal_data['parent'] = self.model_get_parent(parent_global_id)
            except serializers.ValidationError as e:
                raise e

        return internal_data

    def get_related_news_global_id(self, obj):
        """Get the global_id of the related news object."""
        if obj.object:
            return obj.object.global_id
        return None


__all__ = ['V2CommentsSerializer']
