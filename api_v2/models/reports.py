import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from api.models import Profile


class Reports(models.Model):
    class Statuses(models.IntegerChoices):
        INAPPROPRIATE = 1, 'This is off topic'
        COUNTERFEITING = 2, 'This infringes on intellectual property rights'
        HATE = 3, 'Hate speech or symbols'
        PORNOGRAPHY = 4, 'Nudity or sexual activity'
        SPAM = 5, 'This is spam or fraud'
        OTHER = 6, 'Something else'
        ABUSIVE_USER = 7, 'User and user`s content are abusive'

    global_id = models.UUIDField(default=uuid.uuid4, db_index=True)

    status = models.IntegerField(choices=Statuses.choices)

    profile = models.ForeignKey(
        Profile, related_name='profile_reports', on_delete=models.SET_NULL, null=True)

    # Generic fk to different type of News
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.IntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('profile', 'content_type', 'object_id')


__all__ = ['Reports']
