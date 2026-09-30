import time
from django.contrib.contenttypes.models import ContentType
from django.db import models
from rest_framework import generics

from api_v2.models import Comments
from api_v2.models import PublisherNews, UserNews, CuratorNews
from api_v2.serializers import V2CommentsSerializer


class CommentsCreate(generics.CreateAPIView):
    serializer_class = V2CommentsSerializer

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
         # Delay the response by 0.3 seconds, 
         # this ensures comment is created as feed on col_feed database
         # This is temporary solution
        time.sleep(0.3) 
        return response


class CommentsDetailsView(generics.DestroyAPIView):
    serializer_class = V2CommentsSerializer
    lookup_field = 'global_id'

    def get_queryset(self):
        # Get comments where the user is either the author of the comment,
        # or the owner of the news item to which the comment was left

        # get the ID of the news where the user is the owner
        publisher_news_ids = PublisherNews.objects.filter(profile=self.request.user.profile).values_list('id', flat=True)
        user_news_ids = UserNews.objects.filter(profile=self.request.user.profile).values_list('id', flat=True)

        # For CuratorNews profile is a JSONField, so we use a different approach
        curator_news_ids = CuratorNews.objects.filter(
            profile__publisher_id=str(self.request.user.profile.global_id)
        ).values_list('id', flat=True)

        # Get ContentType for each news type
        publisher_news_ct = ContentType.objects.get_for_model(PublisherNews)
        user_news_ct = ContentType.objects.get_for_model(UserNews)
        curator_news_ct = ContentType.objects.get_for_model(CuratorNews)

        return Comments.objects.filter(
            models.Q(profile=self.request.user.profile) |
            models.Q(
                models.Q(content_type=publisher_news_ct, object_id__in=publisher_news_ids) |
                models.Q(content_type=user_news_ct, object_id__in=user_news_ids) |
                models.Q(content_type=curator_news_ct, object_id__in=curator_news_ids)
            )
        )
