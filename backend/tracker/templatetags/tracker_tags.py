from django import template
from django.utils.safestring import mark_safe
import markdown

register = template.Library()


@register.filter(name='markdown')
def markdown_format(text):
    """Позволяет использовать Markdown синтаксис."""

    md = markdown.Markdown(extensions=['extra'])
    return mark_safe(md.convert(text))
