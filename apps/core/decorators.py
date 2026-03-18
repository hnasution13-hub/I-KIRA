"""
Decorators akses berbasis role — i-Kira.

Hierarki bypass:
  Developer (is_superuser, company=None) → bypass SEMUA decorator
  Administrator (role=administrator, company=ada) → bypass semua KECUALI addon_required
  Role lainnya → dicek sesuai decorator
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def _is_elevated(request):
    """Return True jika user adalah Developer atau Administrator."""
    return getattr(request, 'is_developer', False) or getattr(request, 'is_administrator', False)


def role_required(*roles):
    """Batasi akses berdasarkan role. Developer & Administrator selalu bypass."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if _is_elevated(request):
                return view_func(request, *args, **kwargs)
            if request.user.role not in roles:
                messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def hr_required(view_func):
    """Hanya HR Manager, HR Staff, Admin, Administrator, Developer."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if _is_elevated(request):
            return view_func(request, *args, **kwargs)
        if not request.user.is_hr:
            messages.error(request, 'Halaman ini hanya untuk tim HR.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """Hanya Manager ke atas, Administrator, Developer."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if _is_elevated(request):
            return view_func(request, *args, **kwargs)
        if not request.user.is_manager_level:
            messages.error(request, 'Halaman ini hanya untuk level Manager.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Hanya Admin, Administrator, Developer."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if _is_elevated(request):
            return view_func(request, *args, **kwargs)
        if request.user.role not in ('admin', 'administrator'):
            messages.error(request, 'Halaman ini hanya untuk Administrator.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def developer_only(view_func):
    """Khusus Developer saja — Administrator pun tidak bisa akses."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not getattr(request, 'is_developer', False):
            messages.error(request, 'Halaman ini hanya untuk Developer.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
