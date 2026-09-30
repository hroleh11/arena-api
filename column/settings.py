import os
import sys
from datetime import timedelta
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECRET_KEY=(str, 'change_key'),
    DJANGO_ALLOWED_HOSTS=(list, ['*']),

    POSTGRESQL_DATABASE=(str, 'db'),
    POSTGRESQL_USER=(str, 'root'),
    POSTGRESQL_PASSWORD=(str, 'root'),
    POSTGRESQL_HOST=(str, 'localhost'),
    POSTGRESQL_PORT=(int, 7777),

    LANGUAGE_CODE=(str, 'en-us'),
    TIME_ZONE=(str, 'UTC'),

    EMAIL_HOST=(str, "smtp.gmail.com"),
    EMAIL_HOST_USER=(str, "example@email.com"),
    EMAIL_HOST_PASSWORD=(str, "strong_password"),
    EMAIL_PORT=(int, 999),
    DEFAULT_FROM_EMAIL=(str, 'webmaster@localhost'),

    RABBITMQ_URL=(str, "amqp://user:password@localhost:5672/vhost"),

    CORS_ALLOWED_ORIGINS=(list, []),

    AWS_S3_ACCESS_KEY_ID=(str, 'access_key'),
    AWS_S3_SECRET_ACCESS_KEY=(str, 'secret_key'),
    AWS_STORAGE_BUCKET_NAME=(str, 'bucket'),
    AWS_NEWS_STORAGE_BUCKET_NAME=(str, 'new_bucket'),
    AWS_S3_REGION_NAME=(str, 'region_name'),
    AWS_VIDEO_UPLOAD_BUCKET=(str, 'video_bucket'),
    AWS_AUDIO_UPLOAD_BUCKET=(str, 'audio_bucket'),
    AWS_VIDEO_UPLOAD_BUCKET_OPTIMIZED=(str, 'video_bucket'),
    AWS_AUDIO_UPLOAD_BUCKET_OPTIMIZED=(str, 'audio_bucket'),
    AWS_S3_CUSTOM_DOMAIN=(str, 'cdn_domain'),
    AWS_S3_AUDIOVIDEO_CUSTOM_DOMAIN=(str, 'audio-video_cdn_domain'),
    AWS_QUERYSTRING_AUTH=(bool, False),
    AWS_S3_SECURE_URLS=(bool, True),

    SOCIAL_AUTH_FACEBOOK_KEY=(str, 'SOCIAL_AUTH_FACEBOOK_KEY'),
    SOCIAL_AUTH_FACEBOOK_SECRET=(str, 'SOCIAL_AUTH_FACEBOOK_SECRET'),
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=(str, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY'),
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=(str, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET'),
    SOCIAL_AUTH_APPLE_ID_CLIENT=(str, 'SOCIAL_AUTH_APPLE_ID_CLIENT'),
    SOCIAL_AUTH_APPLE_ID_TEAM=(str, 'SOCIAL_AUTH_APPLE_ID_TEAM'),
    SOCIAL_AUTH_APPLE_ID_KEY=(str, 'SOCIAL_AUTH_APPLE_ID_KEY'),
    SOCIAL_AUTH_APPLE_ID_SECRET=(str, 'SOCIAL_AUTH_APPLE_ID_SECRET'),

    APPLE_ID_APP_STORE=(str, 'APPLE_ID_APP_STORE'),
    APPLE_URL_APP_STORE=(str, ''),

    ANDROID_APP_VERSION=(str, ''),
    ANDROID_URL_GOOGLE_STORE=(str, ''),
    ANDROID_PACKAGE_NAME=(str, ''),

    EXTERNAL_IDS_DOMAIN=(str, ''),

    FIREBASE_WEB_API_KEY=(str, ''),
    FIREBASE_URL_PREFIX=(str, ''),

    PROJECT_NAME=(str, ''),
    VYLO_URL=(str, ''),
    JOIN_LINK=(str, '')
)
environ.Env.read_env(env_file=str(BASE_DIR / ".environment"))

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

LINK_JOIN = env('JOIN_LINK')

# Application definition
DJANGO_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)
THIRD_PARTY_APPS = (
    'django_crontab',
    'django_extensions',
    'django_celery_results',
    'rest_framework',
    'drf_yasg',
    'djoser',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'social_django',
)
LOCAL_APPS = (
    'column',
    'api.apps.ApiConfig',
    'api_v2',
)
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'column.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'column.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRESQL_DATABASE'),
        'USER': env('POSTGRESQL_USER'),
        'PASSWORD': env('POSTGRESQL_PASSWORD'),
        'HOST': env('POSTGRESQL_HOST'),
        'PORT': env.int('POSTGRESQL_PORT'),
    }
}
if 'pytest' in sys.argv[0]:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6}
    },
    {
        'NAME': 'column.password_validation.SpecSymbolPasswordValidator',
    },
    {
        'NAME': 'column.password_validation.NumberPasswordValidator',
    },
    {
        'NAME': 'column.password_validation.LetterValidator',
    },
    # {
    #     'NAME': 'column.password_validation.UpperPasswordValidator',
    # },
    # {
    #     'NAME': 'column.password_validation.LowerPasswordValidator',
    # },
    {
        'NAME': 'column.password_validation.BlankValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
LANGUAGE_CODE = env('LANGUAGE_CODE')
TIME_ZONE = env('TIME_ZONE')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_PORT = env('EMAIL_PORT')

CRONJOBS = [
    ('*/60 * * * *', 'api.cron.delete_expired_codes'),
    ('0 0 * * 1', 'api.cron.delete_draft_news'),
    ('* * * * *', 'api.cron.create_personal_link')
]

CELERY_RESULT_BACKEND = 'django-db'
CELERY_BROKER_URL = BROKER_URL = env('RABBITMQ_URL')
CELERY_TASK_DEFAULT_EXCHANGE = "celery"
CELERY_ACCEPT_CONTENT = ["json", 'pickle']
CELERY_TASK_SERIALIZER = "pickle"
CELERY_TASK_QUEUES = {
   "app": {
       "binding_key": "app",
       "priority": True,  # Enable priority support
   },
   "admin": {
       "binding_key": "admin",
       "priority": True,  # Enable priority support
   },
   "lineup_priority": {
       "binding_key": "lineup_priority",
   },
   "events": {
       "binding_key": "events",
   },
   "post_sync_admin": {
       "binding_key": "post_sync_admin",
       "priority": True,
   },
   "post_sync_events": {
       "binding_key": "post_sync_events",
       "priority": True,
   },
   "post_sync_feed": {
       "binding_key": "post_sync_feed",
       "priority": True,
   },
   "post_sync_column": {
       "binding_key": "post_sync_column",
       "priority": True,  # Enable priority support for post synchronization
   }
}
CELERY_IMPORTS = ["column.tasks", "api.tasks"]

CELERY_TASK_ROUTES = {
    # Інші таски залишаються в своїх чергах
    'api.tasks.fetch_lineup_data': {'queue': 'app'},
    'api.tasks.receive_lineup_data': {'queue': 'app'},
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.CursorPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': {'v1'},
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=20),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(days=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),

    "TOKEN_REFRESH_SERIALIZER": "api.serializers.auth.CustomTokenRefreshSerializer",
}

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        "Auth Token eg [Bearer (JWT)]": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header"
        }
    }
}

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_ACCESS_KEY_ID = env('AWS_S3_ACCESS_KEY_ID')
AWS_S3_SECRET_ACCESS_KEY = env('AWS_S3_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_NEWS_STORAGE_BUCKET_NAME = env('AWS_NEWS_STORAGE_BUCKET_NAME')
AWS_VIDEO_UPLOAD_BUCKET = env('AWS_VIDEO_UPLOAD_BUCKET')
AWS_AUDIO_UPLOAD_BUCKET = env('AWS_AUDIO_UPLOAD_BUCKET')
AWS_VIDEO_UPLOAD_BUCKET_OPTIMIZED = env('AWS_VIDEO_UPLOAD_BUCKET_OPTIMIZED')
AWS_AUDIO_UPLOAD_BUCKET_OPTIMIZED = env('AWS_AUDIO_UPLOAD_BUCKET_OPTIMIZED')
AWS_QUERYSTRING_AUTH = env.bool("AWS_QUERYSTRING_AUTH")
AWS_S3_SECURE_URLS = env.bool("AWS_S3_SECURE_URLS")

CDN_DOMAIN_NAME = env('AWS_S3_CUSTOM_DOMAIN')
CDN_AUDIOVIDEO_DOMAIN_NAME = env('AWS_S3_AUDIOVIDEO_CUSTOM_DOMAIN')

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Auth
DJOSER = {
    "LOGIN_FIELD": "email",
    'USER_CREATE_PASSWORD_RETYPE': True,
    'USERNAME_CHANGED_EMAIL_CONFIRMATION': True,
    'PASSWORD_CHANGED_EMAIL_CONFIRMATION': True,
    'PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND': True,
    'USERNAME_RESET_SHOW_EMAIL_NOT_FOUND': True,
    'SEND_CONFIRMATION_EMAIL': False,
    'SET_USERNAME_RETYPE': True,
    'SET_PASSWORD_RETYPE': True,
    'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
    'USERNAME_RESET_CONFIRM_URL': 'email/reset/confirm/{uid}/{token}',
    'ACTIVATION_URL': 'activate/{uid}/{token}',
    'SEND_ACTIVATION_EMAIL': False,
    'SERIALIZERS': {
        'password_reset': 'api.serializers.auth.EmailResetSerializer',
        'password_reset_confirm': 'api.serializers.auth.CustomPasswordResetConfirmSerializer',
        'user_create_password_retype': 'api.serializers.auth.RegisterUserSerializer',
        'user': 'api.serializers.profile.ProfileUserSerializer',
        'user_delete': 'djoser.serializers.UserDeleteSerializer',
        'current_user': 'api.serializers.profile.ProfileUserSerializer',
    },
    'EMAIL': {
        "password_reset": "api.email.PasswordResetEmail",
        "password_changed_confirmation": "api.email.PasswordChangedConfirmationEmail",
    },
    'SOCIAL_AUTH_TOKEN_STRATEGY': 'djoser.social.token.jwt.TokenStrategy',
    'SOCIAL_AUTH_ALLOWED_REDIRECT_URIS': [
        'https://dev.column.artkai.dev/google/',
        'https://dev.column.artkai.dev/facebook/',
    ]
}

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.google.GooglePlusAuth',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.apple.AppleIdAuth',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_FACEBOOK_KEY = env('SOCIAL_AUTH_FACEBOOK_KEY')
SOCIAL_AUTH_FACEBOOK_SECRET = env('SOCIAL_AUTH_FACEBOOK_SECRET')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'fields': 'id, name, email'}

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid',
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ['id', 'name', 'email']

SOCIAL_AUTH_APPLE_ID_CLIENT = env('SOCIAL_AUTH_APPLE_ID_CLIENT')
SOCIAL_AUTH_APPLE_ID_TEAM = env('SOCIAL_AUTH_APPLE_ID_TEAM')
SOCIAL_AUTH_APPLE_ID_KEY = env('SOCIAL_AUTH_APPLE_ID_KEY')
SOCIAL_AUTH_APPLE_ID_SECRET = env.str('SOCIAL_AUTH_APPLE_ID_SECRET', multiline=True)
SOCIAL_AUTH_APPLE_ID_SCOPE = ['email', 'name']
SOCIAL_AUTH_APPLE_ID_EMAIL_AS_USERNAME = True

APPLE_ID_APP_STORE = env('APPLE_ID_APP_STORE')
APPLE_URL_APP_STORE = env('APPLE_URL_APP_STORE')

ANDROID_APP_VERSION = env('ANDROID_APP_VERSION')
ANDROID_URL_GOOGLE_STORE = env('ANDROID_URL_GOOGLE_STORE')
ANDROID_PACKAGE_NAME = env('ANDROID_PACKAGE_NAME')

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'api.pipeline.get_profile_data_and_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'api.pipeline.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

EXTERNAL_IDS_DOMAIN = env('EXTERNAL_IDS_DOMAIN')

FIREBASE_WEB_API_KEY = env('FIREBASE_WEB_API_KEY')
FIREBASE_URL_PREFIX = env('FIREBASE_URL_PREFIX')

PROJECT_NAME = env('PROJECT_NAME')
VYLO_URL = env('VYLO_URL')

UNIVERSAL_CODES = env.list('UNIVERSAL_CODES')

PLATFORMS = env.list('PLATFORMS')

ONESIGNAL_APP_ID = env("ONE_SIGNAL_APP_ID")
ONESIGNAL_APP_KEY = env("ONE_SIGNAL_APP_KEY")
ONESIGNAL_USER_KEY = env("ONE_SIGNAL_USER_KEY")
