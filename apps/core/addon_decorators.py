"""
Decorator untuk cek add-on aktif sebelum akses view.

Hierarki addon:
  Developer   → bypass semua addon (selalu True)
  Administrator → dicek dari AddonLicense Company
  User biasa  → dicek dari AddonLicense Company

Expiry logic:
  valid   → akses penuh
  grace   → akses + warning banner (7 hari setelah expired)
  expired → terkunci, tampil halaman addon_locked
"""
from functools import wraps
from django.shortcuts import render

ADDON_LABELS = {
    'assets':              'Asset Management',
    'recruitment':         'Rekrutmen',
    'psychotest':          'Psikotes',
    'advanced_psychotest': 'Advanced Psychotest (OCEAN)',
    'od':                  'Organisation Development',
    'performance':         'Performance & KPI',
}


def _get_license(company, addon_name):
    """Return AddonLicense for company+addon, or None."""
    if not company:
        return None
    try:
        from apps.core.models import AddonLicense
        return AddonLicense.objects.filter(
            company=company, addon=addon_name, aktif=True
        ).first()
    except Exception:
        return None


def _is_addon_active(company, addon_name):
    """
    True jika addon valid atau dalam grace period.
    Fallback ke Company boolean flag untuk backward compat.
    """
    if not company:
        return False

    # Cek AddonLicense dulu (sistem baru)
    lic = _get_license(company, addon_name)
    if lic is not None:
        return lic.is_valid  # includes grace period

    # Fallback: Company boolean flag (sistem lama / dev setup)
    return bool(getattr(company, f'addon_{addon_name}', False))


def addon_required(addon_name):
    """
    Decorator: cek apakah addon aktif untuk company user.
    Developer bypass. Administrator & user biasa dicek dari AddonLicense.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Developer — bypass semua addon
            if getattr(request, 'is_developer', False):
                return view_func(request, *args, **kwargs)

            company = getattr(request, 'company', None)
            if _is_addon_active(company, addon_name):
                return view_func(request, *args, **kwargs)

            return render(request, 'core/addon_locked.html', {
                'addon_name':  addon_name,
                'addon_label': ADDON_LABELS.get(addon_name, addon_name),
            })
        return wrapper
    return decorator


def check_addon(request, addon_name):
    """
    Helper — return True jika addon aktif (valid atau grace).
    Developer: selalu True.
    """
    if getattr(request, 'is_developer', False):
        return True
    company = getattr(request, 'company', None)
    return _is_addon_active(company, addon_name)


def get_addon_license_context(company):
    """
    Return dict of addon license info untuk context template.
    {
      'addon_name': {
        'aktif': bool,
        'is_grace': bool,
        'days_left': int or None,
        'expiry': date or None,
      }
    }
    """
    from apps.core.models import AddonLicense
    result = {}
    if not company:
        return result

    licenses = AddonLicense.objects.filter(company=company, aktif=True)
    lic_map  = {l.addon: l for l in licenses}

    for addon_name in ADDON_LABELS:
        lic = lic_map.get(addon_name)
        if lic:
            result[addon_name] = {
                'aktif'   : lic.is_valid,
                'is_grace': lic.is_grace,
                'days_left': lic.days_until_expiry,
                'expiry'  : lic.expiry,
                'serial_key': lic.serial_key,
                'aktif_sejak': lic.aktif_sejak,
                'diaktifkan_oleh': lic.diaktifkan_oleh,
            }
        else:
            # Fallback ke Company flag
            flag = bool(getattr(company, f'addon_{addon_name}', False))
            result[addon_name] = {
                'aktif'   : flag,
                'is_grace': False,
                'days_left': None,
                'expiry'  : None,
                'serial_key': '',
                'aktif_sejak': None,
                'diaktifkan_oleh': '',
            }
    return result
