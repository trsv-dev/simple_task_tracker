# Generated by Django 4.2.5 on 2024-03-18 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_alter_profile_telegram_chat_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='bio',
            field=models.TextField(blank=True, default='Не заполнено', help_text='Расскажите немного о себе', null=True, verbose_name='Кратко о себе'),
        ),
    ]