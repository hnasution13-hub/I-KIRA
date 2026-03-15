# ==================================================
# FILE: apps/audit/signals.py
# PATH: D:/Project Pyton/Asset Management Django/apps/audit/signals.py
# DESKRIPSI: Signal untuk mencatat aktivitas user ke AuditLog
# PERBAIKAN: Tambah pengecekan request.user di middleware
# VERSION: 1.0.1
# UPDATE TERAKHIR: 05/03/2026
# ==================================================

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AuditLog
import threading

# Simpan request user di thread local untuk akses di signal
_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

def set_current_user(user):
    _thread_locals.user = user

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set user ke thread local jika ada dan terautentikasi
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)
        response = self.get_response(request)
        return response


@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    # Hanya untuk model dari app kita
    if sender._meta.app_label in ['accounts', 'assets', 'employees', 'vendors', 'locations', 'movements', 'maintenance']:
        user = get_current_user()
        if user and user.is_authenticated:
            action = 'CREATE' if created else 'UPDATE'
            AuditLog.objects.create(
                user=user,
                username=user.username,
                action=action,
                description=f"{sender._meta.verbose_name}: {instance}",
                object_id=instance.pk,
                object_repr=str(instance),
            )

@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    if sender._meta.app_label in ['accounts', 'assets', 'employees', 'vendors', 'locations', 'movements', 'maintenance']:
        user = get_current_user()
        if user and user.is_authenticated:
            AuditLog.objects.create(
                user=user,
                username=user.username,
                action='DELETE',
                description=f"{sender._meta.verbose_name} dihapus: {instance}",
                object_id=instance.pk,
                object_repr=str(instance),
            )