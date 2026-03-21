"""
IKIRA Offline License Engine
─────────────────────────────
Key format : IKIRA-{ADDON}-{HASH8}-{EXPIRY}-{CHECK3}
Example    : IKIRA-RCT-A3F9B2C1-20270321-X7K

Binding    : HMAC-SHA256(IKIRA_LICENSE_SECRET, addon|slug|tanggal_daftar|expiry)
             → key is bound to specific company, cannot be used on another tenant
"""
import hashlib
import hmac
import re
from datetime import date, timedelta

from django.conf import settings

# ── Addon code mapping ────────────────────────────────────────────────────────
ADDON_CODES = {
    'assets':              'AST',
    'advanced_psychotest': 'APY',
    'od':                  'OD0',
}
CODE_TO_ADDON = {v: k for k, v in ADDON_CODES.items()}

ADDON_LABELS = {
    'assets':              'Asset Management',
    'advanced_psychotest': 'Advanced Psychotest (OCEAN)',
    'od':                  'Organisation Development (+ Performance & KPI)',
}

DURATION_CHOICES = [
    ('1m',       '1 Bulan'),
    ('3m',       '3 Bulan'),
    ('6m',       '6 Bulan'),
    ('1y',       '1 Tahun'),
    ('lifetime', 'Lifetime'),
]

GRACE_DAYS = 7
WARN_DAYS  = 30


# ── Key generation ────────────────────────────────────────────────────────────

def _secret():
    return getattr(settings, 'IKIRA_LICENSE_SECRET', settings.SECRET_KEY[:32])


def _expiry_from_duration(duration: str) -> str:
    """Return expiry string YYYYMMDD or 'LIFETIME'."""
    if duration == 'lifetime':
        return 'LIFETIME'
    today = date.today()
    if duration == '1m':
        d = today + timedelta(days=30)
    elif duration == '3m':
        d = today + timedelta(days=90)
    elif duration == '6m':
        d = today + timedelta(days=180)
    elif duration == '1y':
        d = today + timedelta(days=365)
    else:
        d = today + timedelta(days=365)
    return d.strftime('%Y%m%d')


def _make_hash(addon: str, slug: str, tanggal_daftar: str, expiry: str) -> str:
    """Generate 8-char HMAC hash bound to company."""
    payload = f'{addon}|{slug}|{tanggal_daftar}|{expiry}'.lower()
    h = hmac.new(
        _secret().encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    return h[:8].upper()


def _make_checksum(addon_code: str, hash8: str, expiry: str) -> str:
    """3-char checksum for quick tamper detection."""
    payload = f'{addon_code}{hash8}{expiry}'
    h = hmac.new(
        _secret().encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    return h[:3].upper()


def generate_key(addon: str, company) -> str:
    """
    Generate license key for given addon + company.
    company must have .slug and .tanggal_daftar fields.
    """
    from apps.core.models import AddonLicense
    raise NotImplementedError("Use generate_key_with_duration instead")


def generate_key_with_duration(addon: str, company, duration: str) -> str:
    """
    Generate license key for given addon + company + duration.
    Returns formatted key string.
    """
    addon_code   = ADDON_CODES.get(addon)
    if not addon_code:
        raise ValueError(f'Unknown addon: {addon}')

    slug         = company.slug
    tgl_daftar   = company.tanggal_daftar.strftime('%Y%m%d') if company.tanggal_daftar else '00000000'
    expiry       = _expiry_from_duration(duration)
    hash8        = _make_hash(addon, slug, tgl_daftar, expiry)
    checksum     = _make_checksum(addon_code, hash8, expiry)

    return f'IKIRA-{addon_code}-{hash8}-{expiry}-{checksum}'


# ── Key verification ──────────────────────────────────────────────────────────

class LicenseStatus:
    VALID       = 'valid'
    GRACE       = 'grace'      # expired but within grace period
    EXPIRED     = 'expired'    # expired and past grace period
    INVALID     = 'invalid'    # wrong key / tampered
    WRONG_TENANT= 'wrong_tenant'


def verify_key(key: str, company) -> dict:
    """
    Verify license key against company.
    Returns dict:
        {
            'status': LicenseStatus.*,
            'addon': str,
            'expiry': date or None,
            'days_left': int or None,
            'message': str,
        }
    """
    key = key.strip().upper()

    # Parse format
    parts = key.split('-')
    # IKIRA-{CODE}-{HASH8}-{EXPIRY}-{CHECK3}  = 5 parts
    if len(parts) != 5 or parts[0] != 'IKIRA':
        return {'status': LicenseStatus.INVALID, 'addon': None,
                'expiry': None, 'days_left': None,
                'message': 'Format key tidak valid.'}

    _, addon_code, hash8, expiry_str, checksum = parts

    # Resolve addon
    addon = CODE_TO_ADDON.get(addon_code)
    if not addon:
        return {'status': LicenseStatus.INVALID, 'addon': None,
                'expiry': None, 'days_left': None,
                'message': f'Kode addon "{addon_code}" tidak dikenal.'}

    # Verify checksum
    expected_check = _make_checksum(addon_code, hash8, expiry_str)
    if checksum != expected_check:
        return {'status': LicenseStatus.INVALID, 'addon': addon,
                'expiry': None, 'days_left': None,
                'message': 'Key tidak valid atau sudah dimodifikasi.'}

    # Verify HMAC (binding to company)
    slug       = company.slug
    tgl_daftar = company.tanggal_daftar.strftime('%Y%m%d') if company.tanggal_daftar else '00000000'
    expected_hash = _make_hash(addon, slug, tgl_daftar, expiry_str)
    if hash8 != expected_hash:
        return {'status': LicenseStatus.WRONG_TENANT, 'addon': addon,
                'expiry': None, 'days_left': None,
                'message': 'Key ini tidak valid untuk perusahaan ini.'}

    # Check expiry
    if expiry_str == 'LIFETIME':
        return {'status': LicenseStatus.VALID, 'addon': addon,
                'expiry': None, 'days_left': None,
                'message': 'Key valid (Lifetime).'}

    try:
        expiry_date = date(int(expiry_str[:4]), int(expiry_str[4:6]), int(expiry_str[6:8]))
    except (ValueError, IndexError):
        return {'status': LicenseStatus.INVALID, 'addon': addon,
                'expiry': None, 'days_left': None,
                'message': 'Format tanggal expiry tidak valid.'}

    today     = date.today()
    days_left = (expiry_date - today).days

    if days_left >= 0:
        return {'status': LicenseStatus.VALID, 'addon': addon,
                'expiry': expiry_date, 'days_left': days_left,
                'message': f'Key valid. Berlaku hingga {expiry_date.strftime("%d/%m/%Y")}.'}
    elif abs(days_left) <= GRACE_DAYS:
        return {'status': LicenseStatus.GRACE, 'addon': addon,
                'expiry': expiry_date, 'days_left': days_left,
                'message': f'Key expired {abs(days_left)} hari lalu (grace period {GRACE_DAYS} hari).'}
    else:
        return {'status': LicenseStatus.EXPIRED, 'addon': addon,
                'expiry': expiry_date, 'days_left': days_left,
                'message': f'Key expired sejak {expiry_date.strftime("%d/%m/%Y")}.'}
