import requests

from django.conf import settings


def generate_deep_link(link, **kwargs):

    long_link = f'{settings.FIREBASE_URL_PREFIX}?link={link}/?'

    for key, value in kwargs.items():
        long_link += f'{key}={value}&'

    params = {
        'isi': settings.APPLE_ID_APP_STORE,
        'ibi': settings.SOCIAL_AUTH_APPLE_ID_CLIENT,

        'apn': settings.ANDROID_PACKAGE_NAME,
        'afl': settings.ANDROID_URL_GOOGLE_STORE
    }

    for key, value in params.items():
        long_link += f'{key}={value}&'

    res = requests.post("https://firebasedynamiclinks.googleapis.com/v1/shortLinks?key={}".format(
        settings.FIREBASE_WEB_API_KEY
    ), data={
        "longDynamicLink": long_link
    })

    return res.json().get('shortLink') if res.ok else res.json(), res.status_code
