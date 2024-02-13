from comments.models import Comment, CommentImage
from tracker.models import Task, TaskImage


def handle_images(request, object, model):
    """Обработка изображений. Операции с изображениями."""

    images = request.FILES.getlist('image')

    if 'delete_image' in request.POST:
        object.images.all().delete()

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
