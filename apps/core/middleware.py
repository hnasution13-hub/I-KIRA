"""
Middleware Multi-Tenant i-Kira
Inject request.company dan request.user_role_level dari user yang login.

Hierarki:
  - Developer   : is_superuser=True, company=None  → akses semua tenant, bypass all
  - Administrator: role='administrator', company=ada → akses penuh di company sendiri
  - Admin/HR/dst : role lainnya, company=ada        → akses terbatas per role

Developer bisa switch tenant aktif via session['active_tenant_id'].
"""
from apps.core.models import Company


class CompanyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user = request.user
            if user.is_superuser and not getattr(user, 'company', None):
                request.is_developer     = True
                request.is_administrator = False
                active_tid = request.session.get('active_tenant_id')
                if active_tid:
                    try:
                        request.company = Company.objects.get(pk=active_tid)
                    except Company.DoesNotExist:
                        request.session.pop('active_tenant_id', None)
                        request.company = None
                else:
                    request.company = None
            elif getattr(user, 'role', None) == 'administrator' and getattr(user, 'company', None):
                request.company          = user.company
                request.is_developer     = False
                request.is_administrator = True
            else:
                request.company          = getattr(user, 'company', None)
                request.is_developer     = False
                request.is_administrator = False
        else:
            request.company          = None
            request.is_developer     = False
            request.is_administrator = False

        request.is_superadmin = request.is_developer
        response = self.get_response(request)
        return response


_EXEMPT_PREFIXES = (
    '/daftar/', '/upgrade/', '/login/', '/logout/', '/admin/',
    '/static/', '/media/', '/api/', '/karyawan/login/',
    '/karyawan/logout/', '/password-reset/',
)


class PlanCheckMiddleware:
    """
    Cek status plan (trial/demo) setiap request.
    - Trial expired  → redirect ke /upgrade/
    - Suspend        → redirect ke /upgrade/
    Developer (superuser tanpa company) selalu bypass.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if getattr(request, 'is_developer', False):
                return self.get_response(request)
            path = request.path
            if any(path.startswith(p) for p in _EXEMPT_PREFIXES):
                return self.get_response(request)
            company = getattr(request, 'company', None)
            if company:
                if company.is_trial_expired or company.status == 'suspend':
                    from django.shortcuts import redirect
                    return redirect('registration:upgrade')
        return self.get_response(request)
