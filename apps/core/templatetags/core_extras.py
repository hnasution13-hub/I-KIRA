from django import template

register = template.Library()


@register.filter
def getkey(d, key):
    """Get value from dict by key in template. Usage: {{ dict|getkey:key }}"""
    if isinstance(d, dict):
        return d.get(key, '')
    return ''


@register.filter
def abs(value):
    """Return absolute value."""
    try:
        return __builtins__['abs'](int(value)) if isinstance(__builtins__, dict) else __builtins__.__dict__['abs'](int(value))
    except Exception:
        try:
            return -int(value) if int(value) < 0 else int(value)
        except Exception:
            return value
