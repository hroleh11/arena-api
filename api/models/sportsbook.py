import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Count, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce

from api.models import Comments


class SportEvents(models.Model):
    global_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    uid = models.CharField(max_length=255, unique=True, db_index=True)
    category = models.ForeignKey('Categories', on_delete=models.CASCADE, related_name='sport_events')
    category_abbr = models.CharField(max_length=255, null=True)
    home_team_name = models.CharField(max_length=255, default='', blank=True)
    home_team_image = models.ImageField(default='', null=True, blank=True)
    away_team_name = models.CharField(max_length=255, default='', blank=True)
    away_team_image = models.ImageField(default='', null=True, blank=True)
    home_score = models.CharField(max_length=4, null=True, blank=True)
    away_score = models.CharField(max_length=4, null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    market = models.JSONField(default=list, null=True, blank=True)
    commence_time = models.DateTimeField()

    responses = GenericRelation('ColumnNews')
    comments = GenericRelation('Comments')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def final_score(self):  # TODO check start game by commence_time
        is_score = bool(self.home_score is not None and self.away_score is not None)

        if self.is_completed and is_score:
            return f'Final {self.away_score} - {self.home_score}'
        elif not self.is_completed and is_score:
            return f'Game underway'

    @property
    def comments_count(self) -> int:
        column_news_content_type = ContentType.objects.get_for_model(SportEvents)

        nested_comment_counts = Comments.objects.filter(
            response_to=OuterRef('global_id')
        ).values('response_to').annotate(count=Count('pk')).values('count')

        return Comments.objects.filter(
            content_type=column_news_content_type,
            object_id=self.pk
        ).annotate(
            second_depth=Subquery(nested_comment_counts, output_field=models.IntegerField())
        ).aggregate(total=Coalesce(Count('pk'), 0) + Coalesce(Sum('second_depth'), 0))['total']

__all__ = ['SportEvents']