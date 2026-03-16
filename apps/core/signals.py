"""
apps/core/signals.py
Audit log berbasis Django signals untuk model HRIS inti.

Menggunakan thread-local storage untuk mendapatkan user aktif dari request,
sehingga signals bisa mencatat siapa yang melakukan perubahan tanpa perlu
modifikasi di setiap view.

Cara kerja:
1. RequestUserMiddleware (di bawah) menyimpan request.user ke thread-local.
2. Signal post_save / post_delete membaca user dari thread-local.
3. AuditLog dicatat secara otomatis untuk model yang terdaftar di AUDITED_APPS.
"""

import threading
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

# ---------------------------------------------------------------------------
# Thread-local: simpan user aktif per request
# ---------------------------------------------------------------------------
_thread_locals = threading.local()


def get_current_user():
    """Ambil user yang sedang login dari thread-local."""
    return getattr(_thread_locals, 'user', None)


def set_current_user(user):
    """Set user aktif ke thread-local (dipanggil oleh middleware)."""
    _thread_locals.user = user


# ---------------------------------------------------------------------------
# Middleware ringan: set/unset user di thread-local
# Tambahkan 'apps.core.signals.RequestUserMiddleware' ke MIDDLEWARE
# SETELAH 'django.contrib.auth.middleware.AuthenticationMiddleware'
# ---------------------------------------------------------------------------
class RequestUserMiddleware:
    """
    Middleware untuk menyimpan request.user ke thread-local agar bisa
    diakses oleh Django signals tanpa perlu modifikasi di views.

    Tambahkan ke MIDDLEWARE di settings.py:
        'apps.core.signals.RequestUserMiddleware',
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)

        response = self.get_response(request)

        # Bersihkan setelah request selesai (good practice untuk thread pool)
        set_current_user(None)
        return response


# ---------------------------------------------------------------------------
# App label yang di-audit
# ---------------------------------------------------------------------------
AUDITED_APPS = {
    'employees', 'attendance', 'payroll', 'contracts',
    'industrial', 'recruitment', 'psychotest', 'advanced_psychotest',
}


def _create_audit_log(action, sender, instance, extra_detail=''):
    """Helper: buat AuditLog entry. Fail-safe — tidak boleh crash."""
    try:
        from apps.core.models import AuditLog
        user = get_current_user()
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=sender._meta.verbose_name or sender.__name__,
            object_id=instance.pk,
            detail=f"{sender._meta.app_label}.{sender.__name__}: {instance}{extra_detail}",
        )
    except Exception:
        # Jangan biarkan error audit merusak flow utama
        pass


# ---------------------------------------------------------------------------
# Signal receivers
# ---------------------------------------------------------------------------

@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """Catat CREATE atau UPDATE untuk model di AUDITED_APPS."""
    if sender._meta.app_label not in AUDITED_APPS:
        return
    action = 'CREATE' if created else 'UPDATE'
    _create_audit_log(action, sender, instance)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """Catat DELETE untuk model di AUDITED_APPS."""
    if sender._meta.app_label not in AUDITED_APPS:
        return
    _create_audit_log('DELETE', sender, instance, extra_detail=' [DIHAPUS]')


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    """Update last login IP saat login — tidak dicatat ke AuditLog."""
    try:
        ip = _get_ip(request)
        type(user).objects.filter(pk=user.pk).update(last_login_ip=ip)
    except Exception:
        pass




# ---------------------------------------------------------------------------
# Auto-generate ApprovalMatrix saat Position dibuat atau parent diubah
# ---------------------------------------------------------------------------
# Logika:
#   1. Saat jabatan baru dibuat → buat ApprovalMatrix default semua modul
#      dengan approver = parent jabatan (auto-derive)
#   2. Saat parent jabatan diubah → update ApprovalMatrix yang masih auto
#      (belum di-set manual / jabatan_approver masih None)
#   3. Kalau user sudah set manual (jabatan_approver != None) → TIDAK ditimpa
# ---------------------------------------------------------------------------

SEMUA_MODUL = [
    'leave', 'overtime', 'payroll', 'performance',
    'movement', 'recruitment', 'contract', 'sp', 'phk',
]

def _auto_setup_approval_matrix(position):
    """
    Buat atau update ApprovalMatrix default untuk semua modul.
    Hanya menyentuh entry yang belum di-set manual (jabatan_approver=None).
    Entry yang sudah di-set manual tidak akan ditimpa.
    Fail-safe — tidak boleh crash.
    """
    try:
        from apps.core.models import ApprovalMatrix
        if not position.company_id:
            return

        for modul in SEMUA_MODUL:
            # get_or_create — kalau sudah ada, skip (tidak timpa manual)
            obj, created = ApprovalMatrix.objects.get_or_create(
                company=position.company,
                modul=modul,
                jabatan_pemohon=position,
                level_approval=1,
                defaults={
                    'jabatan_approver': None,  # None = auto-derive dari parent
                    'auto_approve_hari': 0,
                    'notif_email': True,
                    'aktif': True,
                }
            )
            # Kalau sudah ada tapi jabatan_approver None (auto) dan parent berubah
            # → tidak perlu update karena auto-derive langsung baca dari Position.parent
    except Exception:
        pass


@receiver(post_save, sender='core.Position')
def position_post_save(sender, instance, created, **kwargs):
    """
    Trigger auto-setup ApprovalMatrix saat jabatan baru dibuat
    atau saat jabatan diupdate (misal parent berubah).
    """
    _auto_setup_approval_matrix(instance)

def _get_ip(request):
    """Ambil IP asli client, perhatikan proxy."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
