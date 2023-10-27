from django import template
from django.utils.safestring import mark_safe
import markdown

register = template.Library()


@register.filter(name='markdown')
def markdown_format(text):
    md = markdown.Markdown(extensions=['extra'])
    return mark_safe(md.convert(text))
