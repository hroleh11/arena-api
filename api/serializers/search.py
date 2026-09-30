from rest_framework import serializers
from api.models import GlobalSearchTrending


class GlobalSearchTrendingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalSearchTrending
        fields = ['id', 'search_string']
