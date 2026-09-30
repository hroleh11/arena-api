from rest_framework import generics, permissions
from api.models import GlobalSearchTrending
from api.serializers.search import GlobalSearchTrendingSerializer


class GlobalSearchTrending(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = GlobalSearchTrendingSerializer
    queryset = GlobalSearchTrending.objects.all()
    pagination_class = None
