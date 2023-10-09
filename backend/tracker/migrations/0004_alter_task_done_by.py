# Generated by Django 4.2.5 on 2023-10-04 16:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tracker', '0003_alter_task_assigned_to'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='done_by',
            field=models.ForeignKey(blank=True, help_text='Выберите пользователя, отметившего задачу выполненной', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='done_by', to=settings.AUTH_USER_MODEL, verbose_name='Выполнил(а)'),
        ),
    ]