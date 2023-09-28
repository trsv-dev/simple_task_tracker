# Generated by Django 4.2.5 on 2023-09-19 07:00

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tags',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True, verbose_name='Тег')),
                ('slug', models.CharField(max_length=30, validators=[django.core.validators.RegexValidator(message='В слаге содержится недопустимый символ', regex='^[-a-zA-Z0-9_]+$')])),
            ],
            options={
                'verbose_name': 'Тег',
                'verbose_name_plural': 'Теги',
            },
        ),
        migrations.CreateModel(
            name='TaskTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.tags')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tracker.task')),
            ],
            options={
                'verbose_name': 'Связь задания и тега',
                'verbose_name_plural': 'Связи заданий и тегов',
            },
        ),
        migrations.AddField(
            model_name='task',
            name='tags',
            field=models.ManyToManyField(help_text='Выберите подходящий тег', related_name='tasks', through='tracker.TaskTag', to='tracker.tags', verbose_name='Тег'),
        ),
    ]