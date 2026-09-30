import uuid

from django.db import models


class ShareIntroEvents(models.Model):
    global_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    profile = models.ForeignKey('Profile', related_name='intro_event', on_delete=models.SET_NULL, null=True)
    news = models.ForeignKey('ColumnNews', related_name='intro_event', on_delete=models.SET_NULL, null=True)
    provider = models.CharField(max_length=32, blank=True, null=True)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)


class GlobalSearchTrending(models.Model):
    search_string = models.CharField(default='', max_length=100,
                                     blank=True, null=True)

    def __str__(self):
        return f'GlobalSearchTrending ID {self.id} Search string {self.search_string}'


__all__ = ['ShareIntroEvents', 'GlobalSearchTrending']