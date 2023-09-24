# Generated by Django 4.2.5 on 2023-09-19 08:33

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_tags_tasktag_task_tags'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tasktag',
            options={'verbose_name': 'Связь', 'verbose_name_plural': 'Связи'},
        ),
        migrations.AlterField(
            model_name='tags',
            name='slug',
            field=models.CharField(max_length=30, unique=True, validators=[django.core.validators.RegexValidator(message='В слаге содержится недопустимый символ', regex='^[-a-zA-Z0-9_]+$')], verbose_name='Слаг'),
        ),
        migrations.AlterField(
            model_name='tasktag',
            name='tag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.tags', verbose_name='Тег'),
        ),
        migrations.AlterField(
            model_name='tasktag',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.task', verbose_name='Задача'),
        ),
    ]
