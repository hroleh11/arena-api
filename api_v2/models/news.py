import uuid
from datetime import datetime

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from polymorphic.models import PolymorphicModel

from api.models import Profile, Categories
from api_v2.models.media import MediaImage, MediaVideo, MediaAudio


class GlobalIDManager(models.Manager):
    def is_global_id_unique(self, global_id):
        return not (
            PublisherNews.objects.filter(global_id=global_id).exists() or
            UserNews.objects.filter(global_id=global_id).exists() or
            CuratorNews.objects.filter(global_id=global_id).exists()
        )

    def get_news_obj(self, global_id):
        """
        Get the news object associated with the given global_id.

        :param global_id: The global ID of the news object.
        :return: The news object if found, otherwise None.
        """
        news_obj = PublisherNews.objects.filter(global_id=global_id).first()
        if news_obj:
            return news_obj

        news_obj = UserNews.objects.filter(global_id=global_id).first()
        if news_obj:
            return news_obj

        news_obj = CuratorNews.objects.filter(global_id=global_id).first()
        if news_obj:
            return news_obj

        raise ObjectDoesNotExist(f"No news object found with global_id '{global_id}'")


class BasicNews(PolymorphicModel):
    class Meta:
        abstract = True

    allowed_media_types = ['image', 'video', 'audio']  # List of allowed media types

    class Statuses(models.IntegerChoices):
        PUBLISHED = 2, 'Published'
        APPROVED = 3, 'Approved'

    global_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    category = models.ForeignKey(
        Categories,
        related_name='category_news',
        on_delete=models.SET_NULL,
        null=True,
        default=None
    )

    title = models.CharField(max_length=300, default='')

    status = models.IntegerField(choices=Statuses.choices)

    external_link = models.URLField(blank=True, null=True, default=None)
    web_external_link = models.URLField(blank=True, null=True, default=None)

    published = models.DateTimeField(default=datetime.now, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    events_counter = models.JSONField(null=True, default=None)

    images = GenericRelation(MediaImage)
    videos = GenericRelation(MediaVideo)

    comments = GenericRelation('Comments')

    objects = GlobalIDManager()

    def __str__(self):
        return f'{self.__class__.__name__}: {self.global_id}'

    def save(self, *args, **kwargs):
        # Checking the uniqueness of global_id through all descendants
        if self.pk is None and not self.__class__.objects.is_global_id_unique(self.global_id):
            raise ValueError("Global ID must be unique across all news types.")
        super().save(*args, **kwargs)

    @property
    def main_media(self):
        """
        A generic property for getting the main media object.
        Child classes can override `allowed_media_types` to restrict the types.
        """
        content_type = ContentType.objects.get_for_model(self)

        media_classes = {
            'image': MediaImage,
            'video': MediaVideo,
            'audio': MediaAudio,
        }

        for media_type in self.allowed_media_types:
            media_class = media_classes.get(media_type)
            if not media_class:
                continue

            main_media = media_class.objects.filter(
                content_type=content_type,
                object_id=self.id,
                is_main=True
            ).first()

            if main_media:
                return main_media

        return None


class PublisherNews(BasicNews):
    allowed_media_types = ['image']

    class Statuses(models.IntegerChoices):
        PUBLISHED = 2, 'Published'
        APPROVED = 3, 'Approved'

    category = models.ForeignKey(
        Categories,
        related_name='publisher_news_category',
        on_delete=models.SET_NULL,
        null=True, default=None
    )
    profile = models.ForeignKey(
        Profile,
        related_name='publisher_news_profile',
        on_delete=models.SET_NULL,
        null=True, default=None
    )

    link = models.URLField(max_length=300, default=None, null=True, blank=True)
    author = models.CharField(max_length=100, null=True, blank=True)
    status = models.IntegerField(choices=Statuses.choices, default=Statuses.APPROVED)

    comments = GenericRelation('Comments')


class UserNews(BasicNews):
    allowed_media_types = ['video', 'audio']

    class Statuses(models.IntegerChoices):
        DRAFT = 1, 'Draft'
        PUBLISHED = 2, 'Published'
        APPROVED = 3, 'Approved'
        DECLINED = 4, 'Declined'
        DELETED = 5, 'Deleted'

    category = models.ForeignKey(
        Categories,
        related_name='user_news_category',
        on_delete=models.SET_NULL,
        null=True, default=None
    )
    profile = models.ForeignKey(
        Profile,
        related_name='user_news_profile',
        on_delete=models.SET_NULL,
        null=True, default=None
    )
    lineup_global_id = models.UUIDField(null=True, default=None)
    status = models.IntegerField(choices=Statuses.choices, default=Statuses.DRAFT)

    audios = GenericRelation(MediaAudio, related_query_name='news_audios')

    comments = GenericRelation('Comments')


class CuratorNews(BasicNews):
    allowed_media_types = ['image', 'video']

    class Statuses(models.IntegerChoices):
        PUBLISHED = 2, 'Published'
        APPROVED = 3, 'Approved'
        DELETED = 5, 'Deleted'

    class Types(models.IntegerChoices):
        TEXT = 1, 'Text'
        AVATAR = 2, 'Avatar'
        PHOTO = 3, 'Photo'
        VIDEO = 4, 'Video'

    category = models.ForeignKey(
        Categories,
        related_name='curator_news_category',
        on_delete=models.SET_NULL,
        null=True, default=None
    )
    # Use profile for curator profile
    profile = models.JSONField(default=dict)
    type = models.IntegerField(choices=Types.choices)
    status = models.IntegerField(choices=Statuses.choices, default=Statuses.APPROVED)

    main_prop = models.JSONField(null=True, default=None)
    props = models.JSONField(default=dict, null=True)

    comments = GenericRelation('Comments')


__all__ = ['BasicNews', 'PublisherNews', 'UserNews', 'CuratorNews']
