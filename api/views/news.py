from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework import generics, permissions, mixins

from api.models import ColumnNews, NewsReport
from api.pagination import PublishedPagination
from api.permissions import IsNewsOwner
from api.serializers import MyColumnNewsSerializer, NewsUpdateSerializer, ColumnNewsReport

User = get_user_model()


class UserNewsList(generics.ListAPIView):
    serializer_class = MyColumnNewsSerializer
    pagination_class = PublishedPagination
    permission_classes = [permissions.IsAuthenticated, ]
    lookup_field = 'global_id'

    def get_queryset(self):
        return ColumnNews.objects.filter(publisher=self.request.user.profile) \
            .exclude(status__in=(ColumnNews.Statuses.DRAFT, ColumnNews.Statuses.DELETED,))


class UserNews(generics.RetrieveAPIView):
    serializer_class = MyColumnNewsSerializer
    permission_classes = [permissions.IsAuthenticated, ]
    lookup_field = 'global_id'
    queryset = ColumnNews.objects.all()


class NewsUpdate(mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsNewsOwner]
    serializer_class = NewsUpdateSerializer
    lookup_field = "global_id"

    def get_object(self):
        global_id = self.kwargs.get(self.lookup_field)

        exclude_status = [ColumnNews.Statuses.DELETED]

        if self.request.method == 'DELETED':
            exclude_status.append(ColumnNews.Statuses.DRAFT)

        objs = ColumnNews.objects.filter(global_id=global_id).exclude(status__in=exclude_status)

        if not objs:
            raise Http404('No News matches the given query.')

        return objs.first()

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(publisher=self.request.user.profile)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.status = ColumnNews.Statuses.DELETED
        instance.save()


class NewsReportView(generics.CreateAPIView):
    queryset = NewsReport.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ColumnNewsReport

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)
