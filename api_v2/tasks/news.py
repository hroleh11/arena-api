from urllib.parse import urlparse

from api.models import Profile, Categories
from api_v2.serializers.importing.news import ImportPublisherNewsSerializer, ImportUserNewsSerializer
from column.celery import app

from api_v2.serializers.importing.curator_news import CuratorNewsImport
from api_v2.models.news import CuratorNews, BasicNews, PublisherNews, UserNews


@app.task(name="column.tasks.move2content", queue="app")
def move2usercontent(news):
    print(news)
    if news['media_id'] is None:
        return
    try:
        profile = Profile.objects.get(global_id=news['publisher_id'])
    except Profile.DoesNotExist:
        # Save user's (created in application) posts only
        return
    news['profile'] = profile.id
    try:
        news['category_code'] = news['category_code']
    except KeyError:
        news['category_code'] = news['category_name'].lower()
    category, created = Categories.objects.get_or_create(
        global_id=news['category_id'],
        defaults={'name': news['category_name'], 'code': news['category_code']}
    )
    news['category'] = category.id
    news['status'] = BasicNews.Statuses.APPROVED

    model = PublisherNews if profile.is_source else UserNews
    try:
        instance = model.objects.get(global_id=news['global_id'])
    except model.DoesNotExist:
        instance = None

    if profile.is_source:
        serializer = ImportPublisherNewsSerializer(instance=instance, data=news)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
    else:
        thumbnail_url = news.pop('thumbnail_url', None)
        if thumbnail_url:
            news['thumbnail_url'] = urlparse(thumbnail_url).path[1:]

        content_url = news.pop('content_url', None)
        if content_url:
            news['content_url'] = urlparse(content_url).path[1:]

        comment = news.get('comment')
        serializer = ImportUserNewsSerializer(
            instance=instance, data=news, context={'profile': profile, 'comment': comment}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()


@app.task(name="column.tasks.curator_news_to_content", queue="app", max_retries=3, bind=True)
def curator_news_to_content(self, data):
    """
    Create or update a CuratorNews object via the update method in the serializer.
    """
    try:
        print(data)
        global_id = data.get("global_id")
        if not global_id:
            raise ValueError("global_id is required to process the news.")

        instance = CuratorNews.objects.filter(global_id=global_id).first()

        if instance:
            serializer = CuratorNewsImport(instance=instance, data=data, partial=True)
            action = "updated"
        else:
            serializer = CuratorNewsImport(data=data)
            action = "created"

        serializer.is_valid(raise_exception=True)

        saved_instance = serializer.save()

        print(f"CuratorNews successfully {action}. Global ID: {saved_instance.global_id}")
        return {"status": "success", "action": action, "global_id": saved_instance.global_id}

    except Exception as exc:
        print(f"Failed to process CuratorNews. Error: {str(exc)}")
        raise self.retry(exc=exc, countdown=5)


@app.task(name="column.tasks.delete_curator_news", queue="app", max_retries=3, bind=True)
def delete_curator_news(self, global_id):
    """
    Deleting a CuratorNews object by its global_id
    """
    try:
        if not global_id:
            raise ValueError("global_id is required to delete the news.")

        instance = CuratorNews.objects.filter(global_id=global_id).first()
        if not instance:
            print(f"CuratorNews with global_id {global_id} not found.")
            return {"status": "not_found", "global_id": global_id}

        instance.images.all().delete()
        instance.videos.all().delete()

        status = CuratorNews.Statuses.DELETED
        objs = CuratorNews.objects.filter(global_id=global_id).exclude(status=status)

        if objs:
            news = objs.first()
            news.status = status
            news.external_link = None
            news.save()
        print(f"CuratorNews with global_id {global_id} successfully deleted.")
        return {"status": "deleted", "global_id": global_id}

    except Exception as exc:
        print(f"Failed to delete CuratorNews with global_id {global_id}. Error: {str(exc)}")
        raise self.retry(exc=exc, countdown=5)
