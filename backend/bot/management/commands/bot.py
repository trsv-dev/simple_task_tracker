import os

from django.core.management import BaseCommand

from bot.bot import main


class Command(BaseCommand):
    """Управление ботом."""

    help = 'Старт бота'

    def add_arguments(self, parser):

        parser.add_argument('action', choices=['start', 'stop'],
                            help='Действие: start - запуск бота, stop - '
                                 'остановка бота')

    def handle(self, *args, **options):

        action = options['action']

        if action == 'start':
            with open('bot/bot_data/bot.pid', 'w') as f:
                f.write(str(os.getpid()))

            main()

        if action == 'stop':
            # Отправляем сигнал завершения процесса
            with open('bot/bot.pid', 'r') as f:
                pid = int(f.read())

            os.kill(pid, 9)
