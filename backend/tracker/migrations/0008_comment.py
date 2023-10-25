# Generated by Django 4.2.5 on 2023-10-23 12:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tracker', '0007_alter_task_deadline_alter_task_is_done'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='Введите текст комментария', verbose_name='Текст комментария')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации комментария')),
                ('author', models.ForeignKey(help_text='Автор комментария', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
                ('parent_comment', models.ForeignKey(blank=True, help_text='Введите ответ на комментарий', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='tracker.comment', verbose_name='Родительский комментарий')),
                ('task', models.ForeignKey(help_text='Комментарий к задаче', on_delete=django.db.models.deletion.CASCADE, to='tracker.task', verbose_name='Задача')),
            ],
            options={
                'verbose_name': 'Комментарий',
                'verbose_name_plural': 'Комментарии',
                'ordering': ['-created'],
            },
        ),
    ]
