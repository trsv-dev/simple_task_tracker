from django.core.exceptions import ValidationError
from django.conf import settings
from comments.models import Comment, CommentImage
from tracker.models import Task, TaskImage


def handle_images(request, object, model):
    """Обработка изображений. Операции с изображениями."""

    images = request.FILES.getlist('image')
    images_count = object.images.count()
    max_images_count = settings.MAX_IMAGES_COUNT


    if len(request.FILES.getlist('image')) > max_images_count:
        raise ValidationError(f'Максимальное количество изображений - '
                              f'{max_images_count}, а вы пытаетесь загрузить '
                              f'{len(images)}.')

    if images_count + len(images) > max_images_count:
        raise ValidationError(f'Максимальное количество изображений - '
                              f'{max_images_count}. Загружено '
                              f'{images_count}, а вы пытаетесь загрузить еще '
                              f'{len(images)}.')

    if model == Task:
        # Создаем список "связок" задачи и изображений.
        task_images = [TaskImage(task=object, image=image) for image in images]
        # Создаем объекты TaskImage одним запросом.
        TaskImage.objects.bulk_create(task_images)

    if model == Comment:
        comment_images = [
            CommentImage(comment=object, image=image) for image in images
        ]
        CommentImage.objects.bulk_create(comment_images)
