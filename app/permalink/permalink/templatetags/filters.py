from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def max_len(text):
    max_length = 100
    if len(text) < max_length:
        return text
    return text[:max_length] + "..."
