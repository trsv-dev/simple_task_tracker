import os
import random

import django
from dotenv import load_dotenv
from telegram import Bot

from tracker.serializers import TaskSerializer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_tracker.settings')
django.setup()

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


def random_greetings():
    """Рандомное приветствие."""

    return random.choice(['Привет', 'Приветствую', 'Доброго времени суток',
                          'Салют', 'Здравствуйте', 'Коничива (яп. "Привет")'])


async def send_telegram_notification(task, chat_id, message_type):
    """Отправка уведомлений о статусе задач в Telegram."""

    try:
        bot = Bot(token=TELEGRAM_TOKEN)

        # user = await sync_to_async(
        #     get_object_or_404)(User, username=context.get('assigned_to'))
        #
        # chat_id = await sync_to_async(
        #     lambda: user.profile.telegram_chat_id)()

        serialized_data = TaskSerializer(task).data

        messages = {
            'create_task': (f'{random_greetings()}, '
                            f'{task.assigned_to}! 👋\n\n'
                            f'Вам была поставлена новая задача: '
                            f'"{task.title}".\n'
                            f'Автор: {task.author}.\n'
                            f'Дата и время дедлайна: '
                            f'{serialized_data["deadline"]}.\n\n'
                            f'Ссылка на задачу: '
                            f'{serialized_data["link"]}.'),
            'deadline': (f'{random_greetings()}, '
                         f'{task.assigned_to}! 👋\n\n'
                         f'Приближается дедлайн по задаче: '
                         f'"{task.title}".\n'
                         f'Дата и время дедлайна: '
                         f'{serialized_data["deadline"]}.\n\n'
                         f'Ссылка на задачу: '
                         f'{serialized_data["link"]}.'),
            'delete_task': (f'{random_greetings()}, '
                            f'{task.assigned_to}! 👋\n\n'
                            f'Задача '
                            f'"{task.title}".\n'
                            f'Была удалена пользователем '
                            f'{task.author}.\n'),
            'done_task': (f'{random_greetings()}, '
                          f'{task.author}! 👋\n\n'
                          f'Созданная вами задача '
                          f'"{task.title}" '
                          f'была выполнена пользователем '
                          f'{task.assigned_to}.\n'
                          f'Дата и время выполнения: '
                          f'{serialized_data["done_by_time"]}.\n\n'
                          f'Ссылка на задачу: '
                          f'{serialized_data["link"]}.'),
            'undone_task': (f'{random_greetings()}, '
                            f'{task.author}! 👋\n\n'
                            f'Созданная вами задача '
                            f'"{task.title}" '
                            f'снова в работе.\n\n'
                            f'Ссылка на задачу: '
                            f'{serialized_data["link"]}.'),
            'new_deadline': (f'{random_greetings()}, '
                             f'{task.assigned_to}! 👋\n\n'
                             f'Время наступления дедлайна по задаче '
                             f'"{task.title}" '
                             f'было изменено на '
                             f'{serialized_data["deadline"]}.\n\n'
                             f'Ссылка на задачу: '
                             f'{serialized_data["link"]}.'),
            'task_reassigned': (f'{random_greetings()}, '
                                f'{task.assigned_to}! 👋\n\n'
                                f'Вам была перенаправлена задача '
                                f'"{task.title}"\n'
                                f'Автор задачи: {task.author}.\n'
                                f'Время наступления дедлайна по задаче '
                                f'"{serialized_data["deadline"]}"\n\n'
                                f'Ссылка на задачу: '
                                f'{serialized_data["link"]}.'),
        }

        await bot.send_message(chat_id, messages[message_type])

    except Exception as e:
        print(f'Произошла ошибка при отправке сообщения в Telegram: {e}')
