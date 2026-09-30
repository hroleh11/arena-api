from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from api.models import ResetCode, ColumnNews, Profile
from api.shortcust import generate_deep_link


def delete_expired_codes():
    ResetCode.objects.filter(updated_at__lte=datetime.now(timezone.utc)-timedelta(minutes=30)).delete()


def delete_draft_news():
    seven_days_ago = datetime.today() - timedelta(days=7)
    ColumnNews.objects.filter(status=ColumnNews.Statuses.DRAFT, created_at__lt=seven_days_ago).delete()


def create_personal_link():
    for profile in Profile.objects.filter(personal_link__isnull=True):
        web_link = 'https://{}/profile/{}'.format(settings.EXTERNAL_IDS_DOMAIN, profile.username)
        personal_link, code = generate_deep_link(web_link, pid=profile.global_id)
        if code == 200:
            profile.personal_link = personal_link
            profile.save()
