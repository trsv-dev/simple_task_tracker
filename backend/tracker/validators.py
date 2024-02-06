from django.core.exceptions import ValidationError
from django.utils import timezone

from tracker.models import DONE


def validate_done_status(obj, need_to_clear_done_fields):
    """
    Валидатор админки.
    Проверяем, что статус 'Выполнено' не выбран вручную без заполнения
    соответствующих полей. Проверяем, что статус 'Выполнено' не изменён
    на другой статус, если заполнены все поля в 'Детали выполнения задачи'.
    """

    required_fields = [obj.is_done, obj.done_by, obj.done_by_time]

    if (obj.status == DONE and not all(required_fields) and
            not need_to_clear_done_fields):
        raise ValidationError('Статус "Выполнено" нельзя выбрать вручную! '
                              'Он присваивается при правильном заполнении '
                              'полей раздела "Детали выполнения задачи" '
                              'валидными данными!')

    if (obj.status != DONE and all(required_fields) and
            need_to_clear_done_fields):
        raise ValidationError('Для изменения статуса "Выполнено" '
                              'необходимо удалить содержимое полей '
                              'раздела "Детали выполнения задачи"')


def validate_done_time(obj):
    """
    Валидатор админки.
    Проверяем, что дата и время отметки задачи как выполненной
    соответствуют требованиям.
    """

    if obj.created:
        created_date = obj.created.strftime("%d %B %Y г. %H:%M")

    if obj.done_by_time and obj.done_by_time > timezone.now():
        raise ValidationError('Время выполнения задачи не может '
                              'быть в будущем!')

    if obj.done_by_time and obj.created > obj.done_by_time:
        raise ValidationError('Время выполнения задачи не может быть '
                              'раньше времени создания задачи '
                              f'({created_date}) !')


def validate_required_fields(required_fields):
    """
    Валидатор админки.
    Проверяем, что при отметке задачи как выполненной заполнены
    все необходимые для этого поля.
    """

    if any(required_fields) and not all(required_fields):
        raise ValidationError('Если отмечаете задачу как "Выполнено" '
                              'ОБЯЗАТЕЛЬНО указывайте выполнившего '
                              'пользователя и дату выполнения не ранее '
                              'даты создания задачи (и не позднее текущей '
                              'даты/времени)! Пользователь и дата, '
                              'выбранные без галочки на отметке '
                              '"Выполнено" будут сброшены')


def validate_deadline_reminder(obj):
    """
    Валидатор админки.
    Проверяем что напоминание о дедлайне соответствует требованиям.
    """

    if obj.deadline_reminder < timezone.now():
        raise ValidationError(
            'Напоминание о дедлайне не может быть в прошлом!'
        )
    elif obj.deadline_reminder > obj.deadline:
        raise ValidationError(
            'Напоминание о дедлайне не может быть позже дедлайна!'
        )
