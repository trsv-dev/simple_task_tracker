import os
from pathlib import Path

from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

# Uncomment this on production and enter your domain name here:
###############################################################################

CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http(s)://your_domain.com').split(', ')

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'you_need_to_set_the_secret_key_in_env')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1, localhost').split(', ')

INTERNAL_IPS = os.getenv('INTERNAL_IPS', '127.0.0.1, localhost').split(', ')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_celery_beat',
    'mptt',
    'sorl.thumbnail',
    'debug_toolbar',

    'core.apps.CoreConfig',
    'tracker.apps.TrackerConfig',
    'users.apps.UsersConfig',
    'images.apps.ImagesConfig',
    'comments.apps.CommentsConfig',
    'favorites.apps.FavoritesConfig',
    'tags.apps.TagsConfig',
    'likes.apps.LikesConfig',
    'bot.apps.BotConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # Uncomment if you need to close project from unregistered users
    # 'task_tracker.middlewares.AuthMiddleware',
]

ROOT_URLCONF = 'task_tracker.urls'

TEMPLATES_DIR = BASE_DIR / 'templates'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'tracker.context_processors.year.year',
                'tracker.context_processors.excluded_urls.excluded_urls',
                'tracker.context_processors.telegram_token.telegram_token',
            ],
        },
    },
]

LOGIN_REDIRECT_URL = '/'

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'collected_static'

STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'

WSGI_APPLICATION = 'task_tracker.wsgi.application'

# SQLite's settings (for local development):
###############################################################################

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL's settings (for production or locally in containers):
###############################################################################

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': os.getenv('POSTGRES_DB', 'django'),
#        'USER': os.getenv('POSTGRES_USER', 'django'),
#        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'you_need_to_set_the_password_in_env'),
#        'HOST': os.getenv('DB_HOST', 'localhost'),
#        'PORT': os.getenv('DB_PORT', 5432)
#    }
#}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-Ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:9000')

TASKS_IN_PAGE = os.getenv('TASKS_IN_PAGE', 10)
MAX_IMAGES_COUNT = int(os.getenv('MAX_IMAGES_COUNT', 5))
DAYS_IN_CALENDAR_PAGE = int(os.getenv('DAYS_IN_CALENDAR_PAGE', 3))
MAX_COMMENTS_DEPTH = int(os.getenv('MAX_COMMENTS_DEPTH', 2))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Sending emails via Yandex mail (Don't work on pythonanywhere.com)
###############################################################################

RECIPIENT_ADDRESS = os.getenv('RECIPIENT_ADDRESS',
                              'your_email_on_yandex@yandex.ru')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.yandex.ru')
EMAIL_PORT = os.getenv('EMAIL_PORT', '465')
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL',
                               'your_email_on_yandex@yandex.ru')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER',
                            'your_email_on_yandex@yandex.ru')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD',
                                'your_strong_email_password')
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND',
                          'django.core.mail.backends.smtp.EmailBackend')

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND',
                                  'redis://127.0.0.1:6379/0')

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = os.getenv(
    'CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP', 'True') == 'True'

CELERY_BROKER_TRANSPORT_OPTIONS = {
    'priority_steps': list(range(10)),
    'queue_order_strategy': 'priority',
}

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# For testing purposes, the deadline is checked every minute.
###############################################################################

CELERY_BEAT_SCHEDULE = {
    'Send_email_about_closer_deadline': {
        'task': 'tracker.utils.send_email_about_closer_deadline',
        'schedule': crontab(),
        'options': {'queue': 'slow_queue'}
    },
}

CACHES = {
    'default': {
        'BACKEND': os.getenv('CACHE_BACKEND',
                             'django.core.cache.backends.redis.RedisCache'),
        'LOCATION': os.getenv('CACHE_LOCATION', 'redis://127.0.0.1:6379/1'),
    }
}

REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_DB = os.getenv('REDIS_DB', '1')

# DB queries debugging
###############################################################################

#LOGGING = {
#    'version': 1,
#    'handlers': {
#        'console': {'class': 'logging.StreamHandler'}
#    },
#    'loggers': {
#        'django.db.backends': {
#            'handlers': ['console'],
#            'level': 'DEBUG'
#        }
#    }
#}
