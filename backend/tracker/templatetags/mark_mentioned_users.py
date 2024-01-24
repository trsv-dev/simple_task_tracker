import re

from django import template

register = template.Library()


@register.filter(name='mentioned_users_replace')
def mentioned_users_replace(comment_text, usernames_profiles_links):
    """
    Выделяем отмеченных через '@' в комментарии пользователей
    ссылкой на профиль.
    """

    for username, profile_link in usernames_profiles_links.items():
        comment_text = re.sub(
            rf'@{username}(?![\w-])',
            f'<a href="{profile_link}">@{username}</a>',
            comment_text
        )

    return comment_text
