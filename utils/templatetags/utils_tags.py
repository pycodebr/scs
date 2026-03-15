from django import template

register = template.Library()


@register.filter
def add_class(field, css_class):
    """Add CSS class to a form field widget."""
    return field.as_widget(attrs={'class': css_class})


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
