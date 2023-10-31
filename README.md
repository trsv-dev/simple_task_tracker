# Simple task tracker

### Трекер задач с простым функционалом


![img.png](img.png)


_Тут будет подробное описание проекта и технологий._
### Запуск проекта в контейнерах Docker (подразумевается, что Docker уже установлен):
Клонируйте репозиторий с **develop веткой** к себе на машину:
```
git clone git@github.com:trsv-dev/simple_task_tracker.git -b develop
```
Перейдите в папку task_tracker:
```
cd simple_task_tracker/backend/task_tracker/
```
И в файле **settings.py** закомментируйте  секцию _'SQLite settings'_ и раскомментируйте
секцию _'PostgreSQL settings'_.

Перейдите на два уровня выше, в корень папки проекта. Для этого два раза выполните:
```
cd ..
```
Из корня папки с проектом выполните команду:
```
docker compose -f docker-compose.yml up -d
```
Дождитесь окончания развертывания, далее выполните копирование статики:
```
docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /app/static/
```
И создайте суперпользователя командой:
```
docker compose -f docker-compose.yml exec backend python manage.py createsuperuser
```
Сайт доступен по http://127.0.0.1:8000, Flower доступен по http://127.0.0.1:5555 
с логином/паролем, заданным вами в .env (по умолчанию - _admin_ / _MySuperStrongPassword_).

### Запуск проекта в dev-режиме
Клонируйте репозиторий с **develop веткой** к себе на машину:
```
git clone git@github.com:trsv-dev/simple_task_tracker.git -b develop
```
Перейдите в папку проекта:
```
cd simple_task_tracker/
```
Установите виртуальное окружение (**если работаете в Linux**):
```
python3.10 -m venv venv
```
Активируйте виртуальное окружение:
```
source venv/bin/activate
```
Установите зависимости из файла requirements.txt:
```
pip install -r requirements.txt
``` 
Выполните миграции:
```
python manage.py migrate
```
Создайте суперпользователя:
```
python manage.py createsuperuser
```
В корне проекта найдите файл **.env.example**, переименуйте в **.env** и заполните своими данными.
Как правило, для разработки там менять ничего не нужно. Чтобы заработала почта, скопируйте и вставьте в
**.env** в раздел "Email settings" следующие данные (тестовый пустой ящик на Яндекс.Почте):
```
#Email settings:
###############################################################################
RECIPIENT_ADDRESS='trsv.dev@yandex.ru'
EMAIL_HOST='smtp.yandex.ru'
EMAIL_PORT=465
EMAIL_USE_SSL=True
DEFAULT_FROM_EMAIL='trsv.dev@yandex.ru'
EMAIL_HOST_USER='trsv.dev@yandex.ru'
EMAIL_HOST_PASSWORD='hzitlzdryltagtly'
EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
```
Переходим в папку **_backend_**:
```
cd /backend
```
И выполняем:
```
python manage.py runserver
```
Сайт доступен по адресу http://127.0.0.1:8000, админ-панель - http://127.0.0.1:8000/admin/

Логиниться можно под данными суперпользователя.

Открываем еще одно окно терминала, скачиваем контейнер с Redis:
```
docker pull redis
```
И запускаем его в режиме демона:
```
docker run -d --name redis -p 6379:6379 redis
```
Запускаем Celery (**_в отдельном окне консоли_**, открытом по тому же пути, т.е. в папке /backend):
```
celery -A task_tracker.celery worker -l info
```
**_Опционально:_** Запуск Flower (**_в отдельном окне консоли_**, открытом по тому же пути, т.е. в папке /backend). Мониторинг задач в celery будет доступен по http://127.0.0.1:5555
```
celery -A task_tracker.celery flower
```

Процесс развертывания готового проекта в дальнейшем будет сведен до одной команды.