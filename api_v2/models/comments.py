import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from rest_framework.exceptions import ValidationError

from api.models import Profile


class Comments(MPTTModel):
    global_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    profile = models.ForeignKey(
        Profile,
        related_name='user_comments',
        on_delete=models.SET_NULL,
        null=True
    )
    text = models.TextField()

    user_news = models.OneToOneField(
        'UserNews', related_name='response_to',
        on_delete=models.CASCADE, default=None, null=True, blank=True
    )

    # Generic fk to different type of News
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='v2_comments')
    object_id = models.IntegerField()
    object = GenericForeignKey('content_type', 'object_id')

    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    # The specific comment being responded to in the nested comment thread
    response_to_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name='replies'
    )
    events_counter = models.JSONField(default=dict, null=True)
    
    # Lineup fields for linking comments to lineups
    lineup_global_id = models.UUIDField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class MPTTMeta:
        order_insertion_by = ['created_at']

    def clean(self):
        if self.parent is not None:
            if self.parent.parent:
                from django.core.exceptions import ValidationError as DjangoValidationError
                raise DjangoValidationError({'parent': "Maximum tree depth 1 level exceeded."})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


__all__ = ['Comments']
