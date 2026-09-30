import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Count, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce


class MediaLinks(models.Model):
    class MediaTypes(models.IntegerChoices):
        VIDEO = 1, 'video'
        AUDIO = 2, 'audio'
        IMAGE = 3, 'image'

    global_id = models.UUIDField(default=uuid.uuid4,
                                 db_index=True)
    column_news = models.ForeignKey('ColumnNews',
                                    related_name='media_links',
                                    on_delete=models.CASCADE,
                                    null=True, default=None)
    title = models.CharField(max_length=100, default='')
    link = models.URLField(max_length=300, null=True, blank=True)
    # TODO: make duration required
    duration = models.IntegerField(default=0, null=True)
    width = models.IntegerField(default=0, null=True)
    height = models.IntegerField(default=0, null=True)

    media_type = models.IntegerField(choices=MediaTypes.choices, null=True)

    content = models.FileField(null=True)
    thumbnail = models.ImageField(null=True)

    origin = models.CharField(max_length=20, default='')

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f'Media: {self.id}'

    @property
    def content_url(self):
        if not self.column_news.publisher.is_source and self.content:
            return f'https://{settings.CDN_AUDIOVIDEO_DOMAIN_NAME}/{self.content}'

    @property
    def content_type(self):
        if self.content:
            return self.content.__str__().split('.')[-1]

    @property
    def thumbnail_url(self):
        news = self.news_of_main_media.all().first()
        if not news.publisher.is_source and self.thumbnail:
            return f'https://{settings.CDN_AUDIOVIDEO_DOMAIN_NAME}/{self.thumbnail}'
        elif self.thumbnail:
            return f'https://{settings.CDN_DOMAIN_NAME}/{self.thumbnail}'

        return self.link

    @property
    def thumbnail_type(self):
        if self.thumbnail:
            return self.thumbnail.__str__().split('.')[-1]
        elif self.link:
            return self.link.__str__().split('.')[-1]


class ColumnNews(models.Model):
    class Statuses(models.IntegerChoices):
        DRAFT = 1, 'Draft'
        PUBLISHED = 2, 'Published'
        APPROVED = 3, 'Approved'
        DECLINED = 4, 'Declined'
        DELETED = 5, 'Deleted'

    class EventsChoices(models.IntegerChoices):
        RESPONSE = 4, 'Response'
        NEWS = 5, 'News'
        FOLLOW = 6, 'Follow'

    class ResponseTypes(models.IntegerChoices):
        NEWS = 1, 'News'
        SPORT_EVENTS = 2, 'SPORT_EVENTS'
        COMMENTS = 3, 'Comments'

    global_id = models.UUIDField(default=uuid.uuid4,
                                 db_index=True)
    category = models.ForeignKey('Categories',
                                 related_name='category_news',
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 default=None)
    publisher = models.ForeignKey('Profile',
                                  related_name='publisher_news',
                                  on_delete=models.SET_NULL,
                                  null=True,
                                  default=None)
    title = models.CharField(max_length=300, default='')
    link = models.URLField(max_length=300, default=None, null=True)
    main_media = models.ForeignKey('MediaLinks',
                                   related_name='news_of_main_media',
                                   on_delete=models.SET_NULL,
                                   null=True, default=None)
    author = models.CharField(max_length=100, default='',
                              blank=True, null=True)
    published = models.DateTimeField(default=datetime.now, null=True)
    status = models.IntegerField(choices=Statuses.choices,
                                 default=Statuses.DRAFT)

    source_id = models.IntegerField(default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    external_link = models.URLField(blank=True, null=True, default=None)
    web_external_link = models.URLField(blank=True, null=True, default=None)

    # video_order_num = models.IntegerField(default=None, null=True)

    response_to = models.UUIDField(default=None, null=True, )
    response_type = models.IntegerField(choices=ResponseTypes.choices,
                                        default=None, null=True, blank=True)
    responses = GenericRelation('ColumnNews')
    comments = GenericRelation('Comments')
    lineup_global_id = models.UUIDField(null=True, default=None)
    lineup_data = models.JSONField(null=True, blank=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL, null=True, default=None
    )
    object_id = models.PositiveIntegerField(null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')
    events_counter = models.JSONField(null=True, default=None)

    def __str__(self):
        return f'News: {self.id} (global_id: {self.global_id})'

    @property
    def comments_count(self) -> int:
        column_news_content_type = ContentType.objects.get_for_model(ColumnNews)

        nested_comment_counts = Comments.objects.filter(
            response_to=OuterRef('global_id')
        ).values('response_to').annotate(count=Count('pk')).values('count')

        return Comments.objects.filter(
            content_type=column_news_content_type,
            object_id=self.pk
        ).annotate(
            second_depth=Subquery(nested_comment_counts, output_field=models.IntegerField())
        ).aggregate(total=Coalesce(Count('pk'), 0) +Coalesce(Sum('second_depth'), 0))['total']



    # TODO remove in next iteration
    @property
    def response_chain(self):
        chain = []
        if self.response_to:
            chain.append(str(self.response_to))

            response_to_response =  getattr(self.content_object, 'response_to', None)
            if response_to_response:
                chain.append(str(response_to_response))

        return chain


class NewsReport(models.Model):
    class Statuses(models.IntegerChoices):
        INAPPROPRIATE = 1, 'This is off topic'
        COUNTERFEITING = 2, 'This infringes on intellectual property rights'
        HATE = 3, 'Hate speech or symbols'
        PORNOGRAPHY = 4, 'Nudity or sexual activity'
        SPAM = 5, 'This is spam or fraud'
        OTHER = 6, 'Something else'
        ABUSIVE_USER = 7, 'User and user`s content are abusive'

    global_id = models.UUIDField(default=uuid.uuid4,
                                 db_index=True)
    status = models.IntegerField(choices=Statuses.choices)
    news_global_id = models.UUIDField()
    profile = models.ForeignKey(
        "Profile", related_name='reports', on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('profile', 'news_global_id',)


class Comments(models.Model):
    class Types(models.IntegerChoices):
        NEWS = 1, 'News'
        SPORT = 2, 'SportBook'
        COMMENTS = 3, 'Comments'

    global_id = models.UUIDField(default=uuid.uuid4,
                                 db_index=True)
    profile = models.ForeignKey('Profile',
                                related_name='comments',
                                on_delete=models.SET_NULL,
                                null=True)
    text = models.TextField()
    comment_type = models.IntegerField(choices=Types.choices)
    response_to = models.UUIDField()

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL, null=True, default=None
    )
    object_id = models.PositiveIntegerField(null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    comments = GenericRelation('Comments')
    responses = GenericRelation('ColumnNews')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    @property
    def response_chain(self):
        chain = [str(self.response_to)]
        response_to_response =  getattr(self.content_object, 'response_to', None)
        if response_to_response:
            chain.append(str(response_to_response))
        return chain

    @property
    def response_type(self):
        return self.comment_type


__all__ = ['MediaLinks', 'ColumnNews', 'NewsReport', 'Comments']
