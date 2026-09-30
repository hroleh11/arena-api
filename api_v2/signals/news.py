from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from typing import Union

from api.models import MediaLinks, ColumnNews, Categories
from api_v2.models import UserNews, PublisherNews
from api_v2.models.media import MediaVideo, MediaAudio, MediaImage
from api_v2.serializers.signals import OldNewsSerializer


def get_lineup_category():
    """
    Get the appropriate category for lineup news.
    First try to get 'PickClips', if not found then get 'Picks'.
    """
    try:
        # Try to get PickClips category first
        return Categories.objects.get(name='PickClips', is_active=True)
    except Categories.DoesNotExist:
        try:
            # Fallback to Picks category
            return Categories.objects.get(name='Picks', is_active=True)
        except Categories.DoesNotExist:
            # If neither exists, return None (will use original category logic)
            return None


@receiver(post_save, sender=UserNews, dispatch_uid="user_news_signal")
@receiver(post_save, sender=PublisherNews, dispatch_uid="publisher_news_signal")
def sync_new_architecture_with_old(sender, instance, created, **kwargs):
    transaction.on_commit(lambda: sync_news(instance, created))


def prepare_user_news_data(instance: UserNews) -> dict:
    try:
        response_to = instance.response_to
        if response_to.response_to_comment:
            response_type = ColumnNews.ResponseTypes.COMMENTS
            response_to_id = response_to.response_to_comment.global_id
            response_object = response_to.response_to_comment
        else:
            response_type = ColumnNews.ResponseTypes.NEWS
            response_object = ColumnNews.objects.filter(global_id=response_to.object.global_id).first()
            response_to_id = response_object.global_id

        content_type = ContentType.objects.get_for_model(response_object).id

    except UserNews.response_to.RelatedObjectDoesNotExist:
        response_to_id = None
        response_type = None
        response_object = None
        content_type = None

    # Determine category - use lineup category if lineup_global_id exists
    category_id = None
    if instance.lineup_global_id:
        lineup_category = get_lineup_category()
        category_id = lineup_category.id if lineup_category else (instance.category.id if instance.category else None)
    else:
        category_id = instance.category.id if instance.category else None

    data = {
        'global_id': instance.global_id,
        'category': category_id,
        'publisher': instance.profile.id,
        'published': instance.published,
        'status': instance.status,
        'external_link': instance.external_link,
        'web_external_link': instance.web_external_link,
        'response_to': response_to_id,
        'content_object': {
            "content_type": content_type if content_type else None,
            "object_id": response_object.id if response_object else None,
        },
        'response_type': response_type,
        'events_counter': instance.events_counter,
        'created_at': instance.created_at,
        'updated_at': instance.updated_at,
        'lineup_global_id': instance.lineup_global_id,
    }

    if instance.title != '':
        data['title'] = instance.title

    main_media = instance.main_media

    if isinstance(main_media, MediaVideo):
        data['media'] = {
            'global_id': main_media.global_id,
            "title": "",
            'width': main_media.width,
            'height': main_media.height,
            'duration': main_media.duration,
            'media_type': MediaLinks.MediaTypes.VIDEO,
            'content': str(main_media.content),
            'thumbnail': str(main_media.thumbnail),
            'created_at': main_media.created_at,
            'updated_at': main_media.updated_at,
            'origin': "user upload"
        }
    elif isinstance(main_media, MediaAudio):
        data['media'] = {
            'global_id': main_media.global_id,
            "title": "",
            'duration': main_media.duration,
            'media_type': MediaLinks.MediaTypes.AUDIO,
            'content': str(main_media.content),
            'thumbnail': str(main_media.thumbnail),
            'created_at': main_media.created_at,
            'updated_at': main_media.updated_at,
            'origin': "user upload"
        }
    else:
        data['media'] = {
            'global_id': instance.global_id, 
            "title": "",
            'width': 0,
            'height': 0,
            'duration': 0,
            'media_type': MediaLinks.MediaTypes.IMAGE,  
            'content': None,
            'thumbnail': None,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
            'origin': "default"
        }
    
    return data


def prepare_publisher_news_data(instance: PublisherNews) -> dict:
    data = {
        'global_id': instance.global_id,
        'link': instance.link,
        'category': instance.category.id if instance.category else None,
        'publisher': instance.profile.id,
        'published': instance.published,
        'status': instance.status,
        'external_link': instance.external_link,
        'web_external_link': instance.web_external_link,
        'events_counter': instance.events_counter,
        'author': instance.author,
        'created_at': instance.created_at,
        'updated_at': instance.updated_at,
    }
    if instance.title != '':
        data['title'] = instance.title

    main_media = instance.main_media
    if isinstance(main_media, MediaImage):
        data['media'] = {
            'global_id': main_media.global_id,
            'title': "",
            'width': main_media.width,
            'height': main_media.height,
            'media_type': MediaLinks.MediaTypes.IMAGE,
            'link': str(main_media.link),
            'created_at': main_media.created_at,
            'updated_at': main_media.updated_at,
            'origin': "user upload"
        }

    return data


def sync_news(instance: Union[UserNews, PublisherNews], created):
    print(f'sync_new_architecture_with_old: {instance.global_id = } {instance.status = } {instance.profile = }')

    if isinstance(instance, UserNews):
        data = prepare_user_news_data(instance)
    else:
        data = prepare_publisher_news_data(instance)

    if created:
        # Creating a record through the serializer
        old_news_serialized = OldNewsSerializer(data=data)
        if old_news_serialized.is_valid(raise_exception=True):
            column_news_instance = old_news_serialized.create(old_news_serialized.validated_data)
            # Mark this instance as synced from new architecture to avoid duplication
            column_news_instance._synced_from_new_architecture = True
            print(f'ColumnNews created for UserNews with global_id: {instance.global_id}')
        else:
            print(f'Error creating ColumnNews: {old_news_serialized.errors}')
    else:
        # Update an existing record using the update method
        column_news = ColumnNews.objects.filter(global_id=instance.global_id).first()
        if column_news:
            # Mark this instance as synced from new architecture to avoid duplication
            column_news._synced_from_new_architecture = True
            old_news_serialized = OldNewsSerializer(column_news, data=data)
            if old_news_serialized.is_valid(raise_exception=True):
                old_news_serialized.update(column_news, old_news_serialized.validated_data)
                print(f'ColumnNews updated for UserNews with global_id: {instance.global_id}')
        else:
            print(f'No matching ColumnNews found for global_id: {instance.global_id}')
