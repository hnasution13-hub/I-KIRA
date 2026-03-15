"""
Decorator untuk cek add-on aktif sebelum akses view.

Hierarki addon:
  Developer   → bypass semua addon (selalu True)
  Administrator → DIKONTROL addon Company (sama seperti user biasa)
  User biasa  → DIKONTROL addon Company

Catatan: Administrator sengaja tidak bypass addon — add-on adalah
fitur berbayar yang dikontrol per Company oleh Developer/bisnis.
"""
from functools import wraps
from django.shortcuts import render

ADDON_LABELS = {
    'assets':              'Asset Management',
    'recruitment':         'Rekrutmen',
    'psychotest':          'Psikotes',
    'advanced_psychotest': 'Advanced Psychotest (OCEAN)',
    'od':                  'Organisation Development',
}


def addon_required(addon_name):
    """
    Decorator: cek apakah addon aktif untuk company user.
    Developer bypass. Administrator & user biasa dicek dari Company flags.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Developer — bypass semua addon
            if getattr(request, 'is_developer', False):
                return view_func(request, *args, **kwargs)

            # Administrator & user biasa — cek addon di Company
            company = getattr(request, 'company', None)
            if company and getattr(company, f'addon_{addon_name}', False):
                return view_func(request, *args, **kwargs)

            return render(request, 'core/addon_locked.html', {
                'addon_name':  addon_name,
                'addon_label': ADDON_LABELS.get(addon_name, addon_name),
            })
        return wrapper
    return decorator


def check_addon(request, addon_name):
    """
    Helper — return True jika addon aktif.
    Developer: selalu True. Administrator & user biasa: cek Company flags.
    """
    if getattr(request, 'is_developer', False):
        return True
    company = getattr(request, 'company', None)
    return bool(company and getattr(company, f'addon_{addon_name}', False))
