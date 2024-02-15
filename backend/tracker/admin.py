from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django_celery_beat.models import (IntervalSchedule, CrontabSchedule,
                                       SolarSchedule, ClockedSchedule,
                                       PeriodicTask)

from tracker.models import Task, DONE, PENDING, \
    IN_PROGRESS, TaskImage
from tracker.validators import validate_done_status, validate_done_time, \
    validate_required_fields, validate_deadline_reminder

admin.site.site_header = "Трекер задач"
admin.site.site_title = "Панель администрирования"
admin.site.index_title = "Добро пожаловать в трекер задач"

# Убираем ненужные модули Celery Beat из админки
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)
admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)


class TaskImageInline(admin.TabularInline):
    model = TaskImage
    extra = 1


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Класс администрирования задач."""

    # Флаг, необходимый валидатору (validate_done_fields) для ситуации,
    # когда хотим очистить поля раздела "Детали выполнения задачи"
    # и задача отмечена как "Выполнено". Флаг показывает, нужно ли очищать
    # поля obj.is_done, obj.done_by, obj.done_by_time перед текущей операцией.
    need_to_clear_done_fields = None

    def show_tags(self, object):
        """Показывать тэги."""

        return '\n'.join(tag.name for tag in object.tags.all())

    show_tags.short_description = 'Теги'

    list_display = (
        'id', 'author', 'get_title', 'get_description', 'show_tags',
        'priority', 'status', 'previous_status', 'assigned_to',
        'created', 'deadline', 'deadline_reminder', 'is_notified',
        'is_done', 'done_by', 'done_by_time')

    fieldsets = (
        ('Информация о задаче', {
            'fields': (
                'author', 'title', 'description',
                'priority', 'status', 'previous_status', 'assigned_to',
                'created', 'deadline', 'deadline_reminder', 'is_notified',
            ),
        }),
        ('Детали выполнения задачи', {
            'description': 'Как правило, здесь вмешательство не требуется. '
                           'Но если помечаете задачу выполненной - '
                           'ОБЯЗАТЕЛЬНО указывайте выполнившего пользователя '
                           'и дату выполнения не ранее даты создания задачи и '
                           'не позднее текущего времени!',
            'fields': ('is_done', 'done_by', 'done_by_time'),
            'classes': ('collapse', 'errornote'),
            # 'classes': ('errornote'),
        }),
    )

    inlines = (TaskImageInline, )

    # readonly_fields = ('get_image',)
    readonly_fields = ('created',)
    search_fields = ('author__username', 'author__email',
                     'description', 'title')
    ordering = ('-created',)

    # inlines = (TagsInLine,)

    def get_title(self, obj):
        """Обрезаем длинные заголовки."""

        return obj.title[:30] + ('...' if len(obj.title) > 30 else '')

    get_title.short_description = 'название'

    def get_description(self, obj):
        """Обрезаем длинные описания."""

        return (obj.description[:40] +
                ('...' if len(obj.description) > 40 else ''))

    get_description.short_description = 'описание'

    # def get_image(self, obj):
    #     """Показываем изображение (если есть)."""
    #
    #     if obj.image:
    #         return format_html(
    #             '<img src="{}" style="max-width: 100px; max-height: 100px; '
    #             'object-fit: cover;" />', object.image.url
    #         )
    #     return 'Нет изображения'
    #
    # get_image.short_description = 'Изображение'

    def get_required_fields(self, obj):
        return [obj.is_done, obj.done_by, obj.done_by_time]

    def get_fieldsets(self, request, obj=None):
        """
        Если добавляем новую задачу, скрываем секцию
        'Детали выполнения задачи'.
        """

        if not obj:
            return (
                ('Информация о задаче', {
                    'fields': (
                        'author', 'title', 'description',
                        'priority', 'status', 'assigned_to',
                        'created', 'deadline', 'deadline_reminder',
                        'is_notified',
                    ),
                }),
            )
        # В противном случае, отображаем полные fieldsets
        return super().get_fieldsets(request, obj)

    def save_model(self, request, obj, form, change):
        """
        Переопределяем сохранение модели задачи при
        редактировании из админки.
        """

        required_fields = self.get_required_fields(obj)

        try:
            # self.validate_done_fields(obj)
            # validate_done_fields(obj, self.need_to_clear_done_fields)

            validate_done_status(obj, self.need_to_clear_done_fields)
            validate_done_time(obj)
            validate_deadline_reminder(obj)
            validate_required_fields(required_fields)

            # Если редактируем объект, а не создаем новый
            if obj.id:
                # Если поля (необходимые для отметки задачи как выполненной)
                # выбраны и до этого в коде выше не возникло к ним претензий,
                # то помечаем задачу как выполненную.

                if all(required_fields):
                    obj.previous_status = obj.status
                    obj.status = DONE
                    self.need_to_clear_done_fields = True

                # Если поля очищены - устанавливаем какие-то
                # начальные значения.
                if (not all(required_fields) and
                        self.need_to_clear_done_fields):
                    obj.status = PENDING
                    obj.previous_status = IN_PROGRESS
                    self.need_to_clear_done_fields = False

        except ValidationError as e:
            self.message_user(request, e.message, messages.ERROR)

            # Сбрасываем все поля is_done, done_by и done_by_time
            # если валидация не прошла.
            obj.is_done = False
            obj.done_by = None
            obj.done_by_time = None

            # Отклоняем сохранение
            return HttpResponseBadRequest(e.message)

        # self.need_to_clear_done_fields = None
        # Вызываем оригинальный метод save_model для сохранения объекта
        super().save_model(request, obj, form, change)

    def response_change(self, request, obj):
        """
        Переопределяем порядок действий при редактировании задачи,
        а конкретнее - при нажатии кнопки 'Сохранить' в режиме
        редактирования задачи. Задача должна остаться на
        странице редактирования.
        """

        if "_save" in request.POST:
            pass

        return HttpResponseRedirect(request.path_info)

    def response_add(self, request, obj, post_url_continue=None):
        """
        Переопределяем метод для обработки ответа после создания задачи.
        """

        try:
            obj.save()
        except ValidationError:
            return HttpResponseRedirect(request.path_info)

        if "_addanother" in request.POST or post_url_continue:
            return super().response_add(request, obj, post_url_continue)

        # Если нажата кнопка "Сохранить" и статус "Выполнено" был выбран,
        # перенаправляем пользователя на страницу редактирования объекта.
        if "_save" in request.POST and obj.status == 'Выполнено':
            return HttpResponseRedirect(request.path_info)

        # В противном случае, перенаправляем на страницу списка объектов.
        return super().response_add(request, obj, post_url_continue)


# @admin.register(TaskTag)
# class TaskTagsAdmin(admin.ModelAdmin):
#     list_display = ('task', 'tag')
#
#
# @admin.register(Tags)
# class TagsAdmin(admin.ModelAdmin):
#     list_display = ('name', 'slug')
#     prepopulated_fields = {'slug': ('name',)}
