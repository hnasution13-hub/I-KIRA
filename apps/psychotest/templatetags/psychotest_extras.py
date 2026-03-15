# apps/psychotest/templatetags/psychotest_extras.py
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Ambil nilai dari dict menggunakan key di Django template.
    Usage: {{ my_dict|get_item:key_var }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
