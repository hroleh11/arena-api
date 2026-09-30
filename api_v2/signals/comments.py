from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from api_v2.models.comments import Comments
from api_v2.serializers.export.comments import CommentSerializer
from column.celery import app


# Using Django signals with disconnect to prevent recursion
@receiver(post_save, sender=Comments)
def export_comments(sender, instance, created, **kwargs):
    if instance.user_news is None and created:
        if instance.lineup_global_id:
            # This is a lineup comment - just send it
            data = CommentSerializer(instance).data
            app.send_task('column.tasks.v2comments2feed', args=[data], queue='post_sync_feed')
            app.send_task('column.tasks.add_comment', args=[data], queue='post_sync_admin')
            app.send_task('column.tasks.comments2events', args=[data], queue='post_sync_events')
            
        elif (instance.object and 
              hasattr(instance.object, 'lineup_global_id') and 
              instance.object.lineup_global_id):
            # This is a comment on a post with lineup - create 2 comments
            
            # 1. Send the main comment (for the post)
            main_data = CommentSerializer(instance).data
            app.send_task('column.tasks.v2comments2feed', args=[main_data], queue='post_sync_feed')
            app.send_task('column.tasks.add_comment', args=[main_data], queue='post_sync_admin')
            app.send_task('column.tasks.comments2events', args=[main_data], queue='post_sync_events')
            
            # 2. Create lineup comment (it will be sent automatically via signal)
            Comments.objects.create(
                profile=instance.profile,
                text=instance.text,
                object=instance.object,
                parent=instance.parent,
                response_to_comment=instance.response_to_comment,
                lineup_global_id=instance.object.lineup_global_id
            )
            
        else:
            # Regular comment (without lineup)
            data = CommentSerializer(instance).data
            app.send_task('column.tasks.v2comments2feed', args=[data], queue='post_sync_feed')
            app.send_task('column.tasks.add_comment', args=[data], queue='post_sync_admin')
            app.send_task('column.tasks.comments2events', args=[data], queue='post_sync_events')


@receiver(post_delete, sender=Comments)
def delete_comments(sender, instance, **kwargs):
    app.send_task('column.tasks.delete_comment', args=[instance.global_id], queue='post_sync_admin')
    app.send_task('column.tasks.v2delete_comment', args=[instance.global_id], queue='post_sync_feed')
    app.send_task('column.tasks.delete_comment', args=[instance.global_id], queue='post_sync_events')
