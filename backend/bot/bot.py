import logging
import sys

import django

from asgiref.sync import sync_to_async
from django.conf import settings
from telegram.ext import (CommandHandler, ApplicationBuilder,
                          MessageHandler, filters)

# Инициализируем Django
django.setup()

# И уже потом импортируем недостающие модули из Django
from users.models import Profile

# Подключаем логирование

# Раскомментировать при разработке
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )


# Раскомментить на продакшне для сохранения лога в файл
# Подключаем логирование в файл
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='test_bot.log',
    filemode='w'
)


# В функции start изменяем её так, чтобы она искала пользователя по
# telegram_username
async def start(update, context):
    """Логика ответа на команду /start."""

    chat = update.effective_chat
    chat_id = chat.id
    username = update.message.chat.username

    # Ищем пользователя по telegram_username
    try:
        profile = await sync_to_async(Profile.objects.get)(
            telegram_username=username)

        profile.telegram_chat_id = chat_id

        await sync_to_async(profile.save)()
        msg = (f'Привет, {username}! ✌️ Вы зарегистрированы на сайте и '
               f'ваш chat_id успешно сохранен. Как только в трекере появятся '
               f'подходящие события - мы вас оповестим!')

    except Profile.DoesNotExist:
        msg = (f'Привет, {username}! ✌️ Мы не нашли ваш Telegram username в '
               f'базе. Если вы зарегистрируетесь на сайте и укажете в профиле '
               f'ваш username в Telegram, то вам начнут приходить '
               f'уведомления о приближающихся дедлайнах и других событиях.')

    await context.bot.send_message(chat_id, msg)


async def default_answer(update, context):
    """Логика ответов на все остальные команды."""

    chat = update.effective_chat
    chat_id = chat.id

    msg = 'Пока я понимаю только команду /start, извините 😔'

    text = update.message.text

    if text != '/start' or text.startswitch('/'):
        await context.bot.send_message(chat_id, msg)


def main():
    """Основная логика работы бота."""

    if not settings.TELEGRAM_TOKEN:
        logging.critical('Отсутствуют необходимые переменные окружения')
        sys.exit(1)
    logging.info(
        'Переменные бота присутствуют'
    )
    logging.info('Запуск бота')

    # создаем экземпляр Application и передаем ему токен бота
    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

    # Добавляем обработчик команды /start и отвечаем одной фразой на
    # другие команды и сообщения
    start_handler = CommandHandler('start', start)
    default_answer_handler = MessageHandler(
        filters.TEXT | filters.COMMAND, default_answer
    )

    application.add_handler(start_handler)
    application.add_handler(default_answer_handler)

    # Начинаем получение обновлений
    application.run_polling()


if __name__ == '__main__':
    main()
