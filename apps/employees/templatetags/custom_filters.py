"""
Custom template filters untuk HRIS SmartDesk.
Filter ini menggantikan penggunaan |split yang tidak ada di Django bawaan.

Cara pakai di template:
    {% load custom_filters %}
    {% for item in "a,b,c"|split:"," %}
"""
from django import template

register = template.Library()


@register.filter(name='split')
def split_filter(value, arg):
    """Split string dengan delimiter. Contoh: "a,b,c"|split:"," """
    return str(value).split(arg)


@register.filter(name='rupiah')
def rupiah(value):
    """Format angka ke Rupiah Indonesia. Contoh: 5000000|rupiah → Rp 5.000.000"""
    try:
        return f"Rp {int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"
