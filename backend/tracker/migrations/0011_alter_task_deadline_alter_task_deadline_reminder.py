# Generated by Django 4.2.5 on 2023-11-22 11:36

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0010_task_deadline_reminder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='deadline',
            field=models.DateTimeField(default=datetime.datetime(2023, 11, 22, 11, 36, 35, 807371, tzinfo=datetime.timezone.utc), validators=[django.core.validators.MinValueValidator(datetime.datetime(2023, 11, 22, 11, 36, 35, 807376, tzinfo=datetime.timezone.utc), message='Дедлайн не может быть в прошлом!')], verbose_name='Дедлайн'),
        ),
        migrations.AlterField(
            model_name='task',
            name='deadline_reminder',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Когда напомнить о дедлайне'),
        ),
    ]