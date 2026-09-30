from urllib.parse import urlparse

from celery.exceptions import MaxRetriesExceededError
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from api.models import (
    ColumnNews, Categories, MediaLinks,
    Profile, BetaRefCode, BetaUsers,
    SportEvents, CreatorSocialAssociation,
    AutoFollow
)
from api.one_signal.api import UserAPI
from api.serializers import tasks
from api_v2.models import Comments
from column.celery import app
from django.utils import timezone
from datetime import datetime


@app.task(name="column.tasks.data_queue_processor", queue="app")
def data_queue_processor(num):
    for i in range(num):
        print(i)


@app.task(name="column.tasks.update_or_create_event", queue="app")
def update_or_create_event(data):
    print('update_or_create_event: ', data)

    try:
        instance = SportEvents.objects.get(global_id=data['global_id'])
    except SportEvents.DoesNotExist:
        instance = None

    serializer = tasks.SportEventsSerializer(data=data, instance=instance)
    if serializer.is_valid(raise_exception=False):
        serializer.save()
    else:
        print(serializer.errors)


def save_main_media(news_instance, media_data):
    try:
        instance = MediaLinks.objects.get(global_id=media_data.get('media_id'))
    except MediaLinks.DoesNotExist:
        instance = None

    thumbnail_url = media_data.pop('thumbnail_url', None)
    if thumbnail_url:
        media_data['thumbnail'] = urlparse(thumbnail_url).path[1:]

    content_url = media_data.pop('content_url', None)
    if content_url:
        media_data['content'] = urlparse(content_url).path[1:]

    media_data['column_news'] = news_instance.id

    serializer = tasks.MediaLinksImportSerializer(instance=instance, data=media_data)
    serializer.is_valid(raise_exception=True)
    media_instance = serializer.save()
    return media_instance


@app.task(name="column.tasks.move2content", queue="post_sync_column")
def move2content(news):
    response_to = news.pop('response_to', None)
    import json
    try:
        print('move2content: ', json.dumps(news, default=str))
    except Exception:
        print('move2content: <unserializable payload>')
    try:
        print('response_to: ', json.dumps(response_to, default=str) if response_to else None)
    except Exception:
        print('response_to: <unserializable>')

    if response_to:
        response_type = response_to.get('feed_type')
        if "props" in response_to:
            response_type = ColumnNews.ResponseTypes.NEWS
        news['response_type'] = response_type
        news['response_to'] = response_to.get('global_id')

    # Normalize published datetime to timezone-aware UTC
    published = news.get('published')
    if published is not None:
        try:
            if isinstance(published, str):
                # Support ISO strings with or without 'Z'
                iso_str = published.replace('Z', '+00:00')
                published_dt = datetime.fromisoformat(iso_str)
            elif isinstance(published, datetime):
                published_dt = published
            else:
                published_dt = None

            if published_dt is not None:
                if timezone.is_naive(published_dt):
                    published_dt = timezone.make_aware(published_dt, timezone.utc)
                else:
                    # Convert to UTC to keep consistency across services
                    published_dt = published_dt.astimezone(timezone.utc)
                news['published'] = published_dt
        except Exception:
            # If parsing fails, drop to default behavior (model default)
            news.pop('published', None)

    try:
        profile = Profile.objects.get(global_id=news['publisher_id'])
    except Profile.DoesNotExist:
        # Save user's (created in application) posts only
        return
    news['publisher'] = profile.id
    news['status'] = ColumnNews.Statuses.APPROVED

    category, created = Categories.objects.get_or_create(
        global_id=news['category_id'],
        defaults={'name': news['category_name']})
    news['category'] = category.id

    # Pass lineup fields through if present
    if 'lineup_global_id' in news and news['lineup_global_id'] is None:
        # normalize explicit null to None
        news['lineup_global_id'] = None
    if 'lineup_data' in news and not news['lineup_data']:
        # keep as None/empty to allow async fetch
        news['lineup_data'] = None

    try:
        instance = ColumnNews.objects.get(global_id=news['global_id'])
    except ColumnNews.DoesNotExist:
        instance = None

    news_serializer = tasks.ColumnNewsTaskSerializer(instance, data=news)
    news_serializer.is_valid(raise_exception=True)
    news_instance = news_serializer.save()
    media_fields = ('thumbnail_type', 'thumbnail_url', 'media_id',
                    'content_type', 'content_url',
                    'content_duration', 'content_width', 'content_height',)
    main_media_instance = save_main_media(news_instance, {key: news.get(key) for key in media_fields})
    news_instance.main_media = main_media_instance
    news_instance.save()


@app.task(name="column.tasks.move_category2column", queue="app")
def move_category2column(category):
    global_id = category.get("global_id")
    print(f"Move category to content {global_id}")
    print(category)
    serializer = tasks.CategoryImportSerializer(data=category)
    if serializer.is_valid(raise_exception=False):
        try:
            serializer.instance = Categories.objects.get(global_id=global_id)
        except Categories.DoesNotExist:
            serializer.instance = None
        serializer.save()
    else:
        print(f'Error move category to content ', serializer.errors)


@app.task(name="column.tasks.delete_category2content", queue="app")
def delete_category2content(global_id):
    print(f'Delete from Categories: Category {global_id}')
    try:
        Categories.objects.get(global_id=global_id).delete()
    except Categories.DoesNotExist:
        print(f'Delete from Categories: Category id={global_id} does not exist')


@app.task(name="column.tasks.profile2app", queue="app")
def import_profiles(profile_data):
    print('profile2app')
    print(profile_data)
        
    try:
        profile_inst = Profile.objects.get(global_id=profile_data.get('global_id'))
        print(f'Found profile - creator_cash in DB: {profile_inst.creator_cash}')
    except Profile.DoesNotExist:
        profile_inst = None

    serializer = tasks.ProfileImportSerializer(profile_inst, data=profile_data)

    if serializer.is_valid():
        inst = serializer.save()
        
        
        
    else:
        print(f'Validation errors: {serializer.errors}')


@app.task(name='column.tasks.move_news2beta', queue="app")
def move_news2beta(user_data):
    data = dict(code=user_data.pop('ref_code'))

    beta_user, created = BetaUsers.objects.update_or_create(email=user_data.pop('email'), defaults=user_data)

    if not beta_user.is_active:
        data['tries'] = 3
    beta_code, created = BetaRefCode.objects.update_or_create(beta_user=beta_user, defaults=data)

    print(beta_code)


@app.task(name='column.task.delete_from_app', queue="app")
def delete_from_app(global_id):
    print(f'Delete from app: news {global_id}')
    status = ColumnNews.Statuses.DELETED
    objs = ColumnNews.objects.filter(global_id=global_id).exclude(status=status)

    if objs:
        news = objs.first()
        news.status = status
        news.external_link = None
        news.save()


@app.task(name='column.task.delete_from_app_list', queue="app")
def delete_from_app_list(global_ids):
    print(f'Delete from app: list news {global_ids}')
    status = ColumnNews.Statuses.DELETED
    ColumnNews.objects.filter(global_id__in=global_ids).update(status=status, external_link=None)


@app.task(name='column.task.report_news', queue="app")
def report_news(global_id):
    print(f'Report from app: news {global_id}')
    status = ColumnNews.Statuses.DECLINED
    objs = ColumnNews.objects.filter(global_id=global_id).exclude(status=status)

    if objs:
        news = objs.first()
        news.status = status
        news.save()


@app.task(name='column.task.delete_profile_app', queue="app")
def delete_profile(global_id):
    print(f'Delete Profile {global_id}')

    try:
        profile = Profile.objects.get(global_id=global_id)
    except Profile.DoesNotExist:
        return Response(
            data={'detail': f'Profile [Global ID: {global_id}] does not exist'},
            status=HTTP_400_BAD_REQUEST)

    del_log = []
    # ReportedProfiles
    i_report_users = profile.i_report_users.all()
    del_log.append({'table': 'i_report_users', 'cnt': i_report_users.count()})
    i_report_users.delete()
    users_reported_me = profile.users_reported_me.all()
    users_reported_me.delete()
    del_log.append({'table': 'users_reported_me', 'cnt': users_reported_me.count()})

    # BlockedProfiles
    i_block_users = profile.i_block_users.all()
    del_log.append({'table': 'i_block_users', 'cnt': i_block_users.count()})
    i_block_users.delete()
    users_block_me = profile.users_block_me.all()
    del_log.append({'table': 'users_block_me', 'cnt': users_block_me.count()})
    users_block_me.delete()

    # NewsReport
    i_report_news = profile.reports.all()
    del_log.append({'table': 'i_report_news', 'cnt': i_report_news.count()})
    i_report_news.delete()

    # NewsReport
    i_report_news = profile.reports.all()
    del_log.append({'table': 'i_report_news', 'cnt': i_report_news.count()})
    i_report_news.delete()

    # News
    news = profile.publisher_news.all()

    # MediaLinks
    media_links_cnt = 0
    for n in news:
        media_links = MediaLinks.objects.filter(column_news=n)
        media_links_cnt += media_links.count()
        media_links.delete()
    del_log.append({'table': 'media_links', 'cnt': media_links_cnt})

    del_log.append({'table': 'news', 'cnt': news.count()})
    news.delete()

    # User
    u = profile.user
    del_log.append({'table': f'user {u.username}', 'cnt': 1})
    u.delete()

    # Profile
    del_log.append({'table': f'profile {profile.name} {profile.global_id}', 'cnt': 1})
    profile.delete()

    # Profile cascade delete:
    # AutoFollow

    print(del_log)


@app.task(name="column.tasks.update_share", queue="app")
def update_share(data):
    print(data)
    serializer = tasks.ShareIntroSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
    else:
        print(f'Error update share ', serializer.errors)


@app.task(name="column.tasks.update_creator_social", queue="app")
def update_creator_social(data):
    print('update_creator_social: ', data)
    try:
        profile = Profile.objects.get(global_id=data['profile_global_id'])
    except Profile.DoesNotExist:
        print(f'Profile {data["profile_global_id"]} does not exist')
        return
    data['profile'] = profile.id

    try:
        instance = CreatorSocialAssociation.objects.get(global_id=data['global_id'])
    except CreatorSocialAssociation.DoesNotExist:
        instance = None

    serializer = tasks.CreatorSocialTasksSerializer(instance=instance, data=data)
    if serializer.is_valid():
        serializer.save()
    else:
        print(f'Error update creator social ', serializer.errors)


@app.task(name='column.tasks.delete_creator_social', queue="app")
def delete_creator_social(global_id):
    print(f'Delete CreatorSocialAssociation {global_id}')
    try:
        association = CreatorSocialAssociation.objects.get(global_id=global_id)
        association.delete()
    except CreatorSocialAssociation.DoesNotExist:
        print(f'Delete CreatorSocialAssociation: CreatorSocialAssociation id={global_id} does not exist')



@app.task(name='column.tasks.auto_follow2app', queue='app')
def auto_follow2app(data):
    print(f'auto_follow2app: {data}')
    try:
        instance = AutoFollow.objects.get(global_id=data['global_id'])
    except AutoFollow.DoesNotExist:
        instance = None

    profile_global_id = data.pop('profile_global_id', None)

    try:
        profile = Profile.objects.get(global_id=profile_global_id)
    except Profile.DoesNotExist:
        print(f'Profile {profile_global_id} does not exist')
        return
    else:
        data['profile'] = profile.id

    serializer = tasks.AutoFollowSerializer(instance=instance, data=data)
    if serializer.is_valid(raise_exception=False):
        serializer.save()
    else:
        print(serializer.errors)


@app.task(name='column.tasks.auto_follow_delete', queue='app')
def auto_follow_delete(global_id):
    print(f'Delete AutoFollow {global_id}')
    try:
        instance = AutoFollow.objects.get(global_id=global_id)
        instance.delete()
    except AutoFollow.DoesNotExist:
        print(f'Delete: AutoFollow id={global_id} does not exist')


@app.task(name='column.tasks.onesignal_categories_subscription', queue='app', bind=True,  max_retries=3, default_retry_delay=60)
def onesignal_categories_subscription(self, global_id):
    print(f'onesignal_categories_subscription: {global_id}')
    try:
        profile = Profile.objects.get(global_id=global_id)
    except Profile.DoesNotExist:
        print(f'Profile {global_id} does not exist')
        return

    user_api = UserAPI()
    status_code, data = user_api.update_user(global_id, {'tags': profile.category_subscriptions()})
    if status_code == 404:
        try:
            raise self.retry(exc=Exception(f'Error update user {global_id}: {status_code} {data}'))
        except MaxRetriesExceededError:
            print(f'Unable to update user {global_id} after maximum retries. Status code: {status_code}, Data: {data}')


@app.task(name='column.tasks.onesignal_create_user', queue='app')
def onesignal_categories_subscription(global_id):
    print(f'onesignal_update_alias: {global_id}')
    try:
        profile = Profile.objects.get(global_id=global_id)
    except Profile.DoesNotExist:
        print(f'Profile {global_id} does not exist')
        return

    user_api = UserAPI()
    status_code, data = user_api.create_user({
        'external_id': str(profile.global_id),
        'email': profile.user.email,
        'username': profile.user.username
    }, {})

    if status_code == 200:
        status_code, data = user_api.create_subscription(profile.global_id, 'Email', profile.user.email)

    if status_code != 200 or status_code != 201:
        profile.is_email_subscribed = False
        profile.save()
        return


@app.task(name='column.tasks.update_events_counters', queue='app')
def update_events_counters(data):
    print('update_events_counters: ', data)
    feed_type = data.get('feed_type', None)
    data = data.get('data', None)

    model_type = {
        1: ColumnNews,
        3: Comments
    }

    model = model_type.get(feed_type, None)

    if not model:
        return

    for obj in data:
        try:
            instance = model.objects.get(global_id=obj['global_id'])
        except model.DoesNotExist:
            instance = None
        else:
            instance.events_counter = obj['events']
            instance.save()
