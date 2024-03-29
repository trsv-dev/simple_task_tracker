# Generated by Django 4.2.5 on 2024-03-21 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_alter_profile_notify_in_telegram_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='telegram_username',
            field=models.CharField(blank=True, help_text='Укажите имя пользователя в Telegram', max_length=250, null=True, verbose_name='Имя пользователя в Telegram'),
        ),
    ]
