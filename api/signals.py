from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete, m2m_changed, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction

from api.email import CreatorInviteEmail
from api.models import (
    ColumnNews, NewsReport, Profile,
    ReportedProfiles, BlockedProfiles, AutoFollow,
    ShareIntroEvents, MediaLinks, CreatorSocialAssociation,
    Comments
)
from api.serializers import signals
from api_v2.models import UserNews
from api_v2.serializers.export.comments import CommentSerializer
from column.celery import app


@receiver(post_save, sender=NewsReport)
def move_news2report(sender, instance, created, **kwargs):
    data = signals.ColumnNewsReportExport(instance).data
    print('move_news2report status={} news_id={} profile_id={}'.format(
        data.get("status"), data.get("news_global_id"), data.get("profile_id")
    ))
    app.send_task('column.tasks.move2report',
                  args=[data],
                  queue='post_sync_admin')


@receiver(post_save, sender=Profile)
def move_profile2admin(sender, instance, created, **kwargs):
    if hasattr(instance, '_is_external') and getattr(instance, '_is_external', False):
        print('Profile save from external service - skipping sync back to admin')
        return

    print(f'Profile save from internal service - syncing to admin, creator_cash: {instance.creator_cash}')
    
    profile = signals.ProfileExportSerializer(instance).data
    app.send_task(
        'column.tasks.profile2admin',
        args=[profile],
        queue='post_sync_admin')
    app.send_task(
        'column.tasks.profile2events',
        args=[profile],
        queue='post_sync_events'
    )


@receiver(m2m_changed, sender=Profile.publishers_subscription.through)
def profile_subscriptions(sender, action, instance, pk_set, **kwargs):
    subscribes = [str(p) for p in Profile.objects.filter(
        pk__in=pk_set).values_list('global_id', flat=True)]
    profile = instance.global_id
    if action == 'post_add' and subscribes:
        app.send_task(
            'column.tasks.profile_add_subscription',
            args=[profile, subscribes],
            queue='post_sync_events'
        )
    elif action == 'post_remove' and subscribes:
        app.send_task(
            'column.tasks.profile_remove_subscription',
            args=[profile, subscribes],
            queue='post_sync_events'
        )


@receiver(m2m_changed, sender=Profile.categories_subscription.through)
def profile_categories_subscription(sender, action, instance, pk_set, **kwargs):
    if action == 'post_add' or action == 'post_remove':
        app.send_task(
            'column.tasks.onesignal_categories_subscription',
            args=[str(instance.global_id)],
            queue='post_sync_column'
        )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, update_fields, **kwargs):
    if created:
        initial_data = dict(
            user=instance,
            is_approved=False
        )
        if hasattr(instance, '_profile'):
            initial_data.update(instance._profile)

        profile = Profile.objects.create(**initial_data)

        if profile.is_creator:
            context = {"password": instance._password}
            to = [instance.email]
            CreatorInviteEmail(request=None, context=context).send(to)

        if not profile.is_source:
            # profile.categories_subscription.set(Categories.objects.filter(is_active=True))
            profile.publishers_subscription.set(AutoFollow.objects.values_list('profile', flat=True))

        app.send_task(
            'column.tasks.onesignal_create_user',
            args=[str(profile.global_id)],
            queue='app'
        )

    if update_fields is not None and 'is_active' in update_fields:
        global_id = instance.profile.global_id
        app.send_task('column.tasks.deactivate_profile',
                      args=[global_id],
                      queue='post_sync_admin')
    elif update_fields is not None and 'last_login' in update_fields:
        global_id = instance.profile.global_id
        data = {
            'global_id': global_id,
            'last_login': instance.last_login.isoformat(),
        }
        app.send_task(
            'column.tasks.update_profile_login_info',
            args=[data],
            queue='post_sync_admin'
        )


@receiver(post_save, sender=ColumnNews)
def move_news2admin(sender, instance, created, **kwargs):
    import logging
    from datetime import datetime
    
    # Налаштування логування для синхронізації постів
    logger = logging.getLogger('post_sync.column_api')
    
    logger.info(f'🔄 POST_SYNC: ColumnNews signal triggered - ID: {instance.id}, Status: {instance.status}, Author: {instance.author}, Global ID: {instance.global_id}')

    # Skip if this ColumnNews was created by sync_news to avoid duplication
    if hasattr(instance, '_synced_from_new_architecture'):
        logger.info(f"⏭️  POST_SYNC: Skipping ColumnNews {instance.pk} - synced from new architecture to avoid duplication")
        return

    if instance.lineup_global_id and not instance.lineup_data:
        logger.warning(f"⚠️  POST_SYNC: Skipping ColumnNews {instance.pk} - has lineup_global_id but no lineup_data")
        return
    
    if instance.status in [ColumnNews.Statuses.PUBLISHED, ColumnNews.Statuses.APPROVED]:
        logger.info(f"✅ POST_SYNC: Processing ColumnNews {instance.pk} with status {instance.get_status_display()}")
        
        start_time = datetime.now()
        
        news_serialized = signals.ColumnNewsExportSerializer(instance).data
        logger.info(f"📦 POST_SYNC: Serialized ColumnNews {instance.pk} data successfully")

        new_model_news = UserNews.objects.filter(global_id=instance.global_id).first()

        try:
            comment = new_model_news.response_to
            if new_model_news.response_to:
                news_serialized['comment'] = CommentSerializer(comment).data
                logger.info(f"💬 POST_SYNC: Added comment data for ColumnNews {instance.pk}")
        except UserNews.response_to.RelatedObjectDoesNotExist:
            logger.info(f"ℹ️  POST_SYNC: No comment data for ColumnNews {instance.pk}")
            pass

        # Send to admin for processing with HIGHEST priority using post_sync_admin queue
        task_result = app.send_task('column.tasks.move2approve',
                      args=[news_serialized],
                      queue='post_sync_admin',  # Використовуємо спеціалізовану чергу admin
                      priority=0)  # HIGHEST priority for posts (0=highest)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"🚀 POST_SYNC: Sent ColumnNews {instance.pk} to admin queue - Task ID: {task_result.id}, Processing time: {processing_time:.3f}s")

        if instance.response_to:
            events_task = app.send_task('column.tasks.system_events',
                          args=[{
                              "profile_global_id": str(instance.publisher.global_id),
                              "response_to": str(instance.response_to),
                              "response_type": instance.response_type,
                              "event": 4
                          }], queue='post_sync_events')
            logger.info(f"📢 POST_SYNC: Sent system event for ColumnNews {instance.pk} response via post_sync_events - Task ID: {events_task.id}")
    else:
        logger.info(f"⏸️  POST_SYNC: ColumnNews {instance.pk} status {instance.get_status_display()} - no sync needed")

    if instance.status == ColumnNews.Statuses.DELETED:
        app.send_task('column.task.delete_from_admin',
                      args=[instance.global_id],
                      queue='post_sync_admin')


@receiver(post_save, sender=ReportedProfiles)
def move_reported_profile2admin(sender, instance, created, **kwargs):
    print(
        f'move_reported_profile2admin {instance.reported_profile} {instance.status = }')
    report_serializer = signals.ReportedProfilesExportSerializer(instance).data
    app.send_task('column.tasks.move_reported_profile2admin',
                  args=[report_serializer], queue='post_sync_admin')


@receiver(post_save, sender=BlockedProfiles)
def move_blocked_profile2feed(sender, instance, created, **kwargs):
    print(
        f'move_blocked_profile2feed {instance.blocked_profile}')
    blocked_serializer = signals.BlockedProfilesExportSerializer(instance).data
    app.send_task('column.tasks.move_blocked_profile2feed',
                  args=[blocked_serializer], queue='post_sync_feed')


@receiver(post_delete, sender=BlockedProfiles)
def delete_blocked_profile2feed(sender, instance, *args, **kwargs):
    app.send_task(
        'column.tasks.delete_blocked_profile2feed',
        kwargs={
            "profile_global_id": instance.profile.global_id,
            "blocked_profile_global_id": instance.blocked_profile.global_id,
        },
        queue='post_sync_feed')


@receiver(post_save, sender=ShareIntroEvents)
def share_social_platform(sender, instance, created, **kwargs):
    data = signals.ShareIntroSerializer(instance=instance).data
    app.send_task('column.tasks.update_share', args=[data], queue='post_sync_feed')


@receiver(pre_save, sender=MediaLinks)
def define_media_type(sender, instance, **kwargs):
    if instance.media_type:
        return instance

    if instance.content:
        content_type = {
            'mp4': 1,
            'mp3': 2,
        }
        instance.media_type = content_type.get(instance.content_type, None)


@receiver(post_save, sender=CreatorSocialAssociation)
def update_creator_social(instance, created, *args, **kwargs):
    if created:
        data = signals.CreatorSocialSignalSerializer(instance=instance).data
        app.send_task('column.tasks.create_creator_social', args=[data], queue='post_sync_admin')


@receiver(post_delete, sender=CreatorSocialAssociation)
def delete_creator_social(instance, *args, **kwargs):
    app.send_task('column.tasks.delete_creator_social', args=[instance.global_id], queue='post_sync_admin')


# TODO In case single responsibility, this function should only count comments
def send_amount_comments(response_obj, response_type):  # Comment, ColumnNews, SportEvent
    if response_type == 1 or response_type == 2:  # is_news or is_sport
        responses_counter = response_obj.comments_count
        # TODO currently news comments disabled but this will not work in another case
        responses_counter += response_obj.responses.filter(status=ColumnNews.Statuses.APPROVED).count()
    elif response_type == 3:  # is_comment
        responses_counter = response_obj.comments.count()
        if response_obj.content_object:
            send_amount_comments(response_obj.content_object, response_obj.response_type)
    else:
        print('Unknown response_type')  # TODO log and raise error
        return

    if response_type == 2 or response_type == 3:  # is_sport or is_comment
        app.send_task('column.tasks.update_responses_counter',
                      args=[{
                          'global_id': str(response_obj.global_id),
                          'obj_type': response_type,
                          'responses_counter': responses_counter,
                          'update_time': timezone.now()
                      }],
                      queue='post_sync_feed')
    elif response_type == 1:  # is_news
        app.send_task('column.tasks.update_responses_counter',
                      args=[{
                          'global_id': str(response_obj.global_id),
                          'obj_type': response_type,
                          'responses_counter': responses_counter,
                          'update_time': timezone.now()
                      }],
                      queue='post_sync_admin')


@receiver(post_save, sender=Comments)
def move_comments2admin(sender, instance, created, **kwargs):
    data = signals.CommentsExportSerializer(instance).data
    app.send_task('column.tasks.add_comment',
                  args=[data], queue='post_sync_admin')

    if created:
        app.send_task('column.tasks.system_events',
                      args=[{
                          "profile_global_id": str(instance.profile.global_id),
                          "response_to": str(instance.response_to),
                          "response_type": instance.response_type,
                          "event": 8
                      }], queue='post_sync_events')

        send_amount_comments(instance.content_object, instance.response_type)


@receiver(post_delete, sender=Comments)
def delete_comments2admin(sender, instance, **kwargs):
    print(instance.global_id)
    if instance.content_object:
        send_amount_comments(instance.content_object, instance.response_type)
    app.send_task('column.tasks.delete_comment',
                  args=[str(instance.global_id)], queue='post_sync_admin')


@receiver(post_save, sender=ColumnNews)
def fetch_lineup_data_on_save(sender, instance, created, **kwargs):
    """
    Fetch lineup data when ColumnNews is created or lineup_global_id is updated
    """
    # Fetch lineup data if:
    # 1. lineup_global_id exists
    # 2. lineup_data is empty/None
    # 3. Either it's a new record OR lineup_global_id was updated
    should_fetch = False
    
    if instance.lineup_global_id and not instance.lineup_data:
        if created:
            # New record with lineup_global_id
            should_fetch = True
            print(f"New ColumnNews {instance.pk} created with lineup_global_id {instance.lineup_global_id}")
        elif kwargs.get('update_fields') and 'lineup_global_id' in kwargs.get('update_fields', []):
            # lineup_global_id was explicitly updated
            should_fetch = True
            print(f"ColumnNews {instance.pk} lineup_global_id updated to {instance.lineup_global_id}")
        elif not created:
            # General update case - check if lineup_global_id exists but no data
            should_fetch = True
            print(f"ColumnNews {instance.pk} updated, checking lineup_global_id {instance.lineup_global_id}")
    
    if should_fetch:
        from api.tasks import fetch_lineup_data
        # Use transaction.on_commit to ensure the instance is saved before the task runs
        transaction.on_commit(
            lambda: fetch_lineup_data.delay(instance.pk, str(instance.lineup_global_id))
        )
        print(f"Scheduled lineup data fetch for ColumnNews {instance.pk} with lineup_global_id {instance.lineup_global_id}")
