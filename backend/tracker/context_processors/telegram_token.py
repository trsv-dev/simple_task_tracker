from django.conf import settings


def telegram_token(request):
    return {
        'telegram_token': settings.TELEGRAM_TOKEN
    }
