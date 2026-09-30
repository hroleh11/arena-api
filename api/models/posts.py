import uuid
from django.db import models


class Post(models.Model):
    global_id = models.UUIDField(default=uuid.uuid4, db_index=True)

    response_to = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='responses', null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ColumnNewsV2(Post):
    title = models.CharField(max_length=300, default='')


class CommentsV2(Post):
    profile = models.ForeignKey('Profile',
                                related_name='commentsv2',
                                on_delete=models.SET_NULL,
                                null=True)
    text = models.TextField()



__all__ = ['Post']
