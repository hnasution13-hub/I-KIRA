from rest_framework.permissions import BasePermission


class IsHROrAdmin(BasePermission):
    """Hanya HR Staff, HR Manager, dan Admin yang bisa akses"""
    message = 'Akses ditolak. Hanya tim HR yang diizinkan.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['admin', 'hr_manager', 'hr_staff']
        )


class IsManagerOrAdmin(BasePermission):
    """Hanya Manager ke atas yang bisa akses"""
    message = 'Akses ditolak. Hanya level Manager yang diizinkan.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['admin', 'hr_manager', 'manager']
        )


class IsAdminOnly(BasePermission):
    """Hanya Admin"""
    message = 'Akses ditolak. Hanya Administrator yang diizinkan.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


class IsOwnerOrHR(BasePermission):
    """Karyawan hanya bisa lihat datanya sendiri, HR bisa lihat semua"""
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['admin', 'hr_manager', 'hr_staff']:
            return True
        # Cek apakah object milik user ybs
        if hasattr(obj, 'employee'):
            return obj.employee.nik == request.user.nik
        return False


class ReadOnlyOrHR(BasePermission):
    """Read-only untuk semua user terauth, write hanya untuk HR"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.role in ['admin', 'hr_manager', 'hr_staff']
