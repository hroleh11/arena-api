import uuid

from django.db import models

from api.models import Profile


class ShareIntroEvents(models.Model):
    global_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    profile = models.ForeignKey(Profile, related_name='profile_intro_event', on_delete=models.SET_NULL, null=True)
    news = models.ForeignKey('UserNews', related_name='intro_event', on_delete=models.SET_NULL, null=True)
    provider = models.CharField(max_length=32, blank=True, null=True)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)


__all__ = ['ShareIntroEvents']
