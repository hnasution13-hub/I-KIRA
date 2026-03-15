from django import template
register = template.Library()

@register.filter
def enumerate(lst, start=0):
    return builtins_enumerate(lst, start)

@register.filter
def get_item(dictionary, key):
    """Ambil nilai dari dict dengan key — dipakai di attendance_bulk."""
    return dictionary.get(key)

# avoid shadowing builtin
import builtins
builtins_enumerate = builtins.enumerate
