import os

import django
from asgiref.sync import sync_to_async
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from telegram import Bot

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_tracker.settings')
django.setup()

from users.models import User

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


async def send_telegram_notification(context):
    """Отправка уведомлений о статусе задач в Telegram."""

    try:
        bot = Bot(token=TELEGRAM_TOKEN)

        user = await sync_to_async(
            get_object_or_404)(User, username=context.get('assigned_to'))

        chat_id = await sync_to_async(lambda: user.profile.telegram_chat_id)()

        text = (f'Привет, {context.get("assigned_to")}! 👋\n\n'
                f'Приближается дедлайн по задаче: '
                f'{context.get("title")}.\n'
                f'Дата и время дедлайна: {context.get("deadline")}.\n'
                f'Ссылка на задачу: {context.get("link")}.')

        await bot.send_message(chat_id, text)

    except Exception as e:
        print(f'Произошла ошибка при отправке сообщения в Telegram: {e}')
