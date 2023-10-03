# Generated by Django 4.2.5 on 2023-10-03 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0009_task_done_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='done_by_time',
            field=models.DateTimeField(blank=True, help_text='Время, когда задача была отмечена выполненной', null=True, verbose_name='Время выполнения'),
        ),
    ]
