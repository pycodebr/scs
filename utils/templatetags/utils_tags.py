from decimal import Decimal, InvalidOperation

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def add_class(field, css_class):
    """Add CSS class to a form field widget."""
    return field.as_widget(attrs={'class': css_class})


@register.filter
def brl(value):
    """Format a numeric value as Brazilian Real (R$ 1.234,56)."""
    if value is None or value == '':
        return 'R$ 0,00'
    try:
        value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return 'R$ 0,00'
    negative = value < 0
    value = abs(value)
    cents = value % 1
    integer_part = int(value)
    cents_str = f'{cents:.2f}'[2:]
    int_str = f'{integer_part:,}'.replace(',', '.')
    formatted = f'R$ {int_str},{cents_str}'
    if negative:
        formatted = f'-{formatted}'
    return formatted


@register.simple_tag
def active_url(request, url_name, css_class='active'):
    """Return css_class if current URL matches url_name."""
    from django.urls import resolve
    try:
        current = resolve(request.path_info).url_name
        if current == url_name:
            return css_class
    except Exception:
        pass
    return ''


@register.simple_tag
def active_url_startswith(request, path_prefix, css_class='active'):
    """Return css_class if current path starts with path_prefix."""
    if request.path.startswith(path_prefix):
        return css_class
    return ''
