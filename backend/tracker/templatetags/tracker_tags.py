import bleach
import markdown
from bleach_allowlist import markdown_tags, markdown_attrs
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='markdown')
def markdown_format(text):
    """Позволяет использовать Markdown синтаксис."""

    md = markdown.Markdown(extensions=['extra'])
    return mark_safe(bleach.clean(md.convert(text),
                                  markdown_tags, markdown_attrs))
