"""
Utility helpers untuk multi-tenant i-Kira.
"""
from django.http import Http404


def company_filter(request):
    """
    Return dict filter berdasarkan company user.
    Gunakan dengan .filter(**company_filter(request))
    
    Contoh:
        qs = Employee.objects.filter(**company_filter(request))
        qs = Attendance.objects.filter(employee__company=request.company)
    """
    company = getattr(request, 'company', None)
    if company:
        return {'company': company}
    return {}


def employee_company_filter(request):
    """Filter untuk model yang FK ke Employee (bukan langsung ke Company)."""
    company = getattr(request, 'company', None)
    if company:
        return {'employee__company': company}
    return {}


def get_company_qs(model, request, **extra_filters):
    """
    Return queryset model yang sudah difilter by company.
    
    Contoh:
        employees = get_company_qs(Employee, request, status='Aktif')
        shifts    = get_company_qs(Shift, request)
    """
    company = getattr(request, 'company', None)
    qs = model.objects.all()
    if company:
        qs = qs.filter(company=company)
    if extra_filters:
        qs = qs.filter(**extra_filters)
    return qs


def get_employee_related_qs(model, request, **extra_filters):
    """
    Return queryset model yang FK ke Employee, difilter by employee__company.
    Untuk: Attendance, Leave, Contract, Payroll, dll.
    """
    company = getattr(request, 'company', None)
    qs = model.objects.all()
    if company:
        qs = qs.filter(employee__company=company)
    if extra_filters:
        qs = qs.filter(**extra_filters)
    return qs


def get_tenant_object(model, request, **lookup):
    """
    Ambil single object dengan enforced tenant isolation.
    - Jika request.company ada: pastikan object milik company tersebut.
    - Jika developer (company=None): bypass, ambil langsung.
    Raise Http404 jika tidak ditemukan atau beda tenant.

    Contoh:
        contract = get_tenant_object(Contract, request, pk=pk)
        leave    = get_tenant_object(Leave, request, pk=pk)
    """
    company = getattr(request, 'company', None)
    try:
        obj = model.objects.get(**lookup)
    except model.DoesNotExist:
        raise Http404(f'{model.__name__} not found.')
    except model.MultipleObjectsReturned:
        raise Http404(f'Multiple {model.__name__} returned.')

    if company is None:
        # Developer: bypass tenant check
        return obj

    # Cek apakah object punya field 'company' langsung
    if hasattr(obj, 'company_id'):
        if obj.company_id != company.pk:
            raise Http404(f'{model.__name__} not found.')
        return obj

    # Cek lewat employee__company (untuk model seperti Leave, Attendance, dll)
    if hasattr(obj, 'employee') and obj.employee is not None:
        if hasattr(obj.employee, 'company_id') and obj.employee.company_id != company.pk:
            raise Http404(f'{model.__name__} not found.')
        return obj

    return obj


def get_tenant_employee(request, **lookup):
    """
    Shortcut: ambil Employee dengan tenant isolation.
    Raise Http404 jika employee bukan milik company user.
    """
    from apps.employees.models import Employee
    return get_tenant_object(Employee, request, **lookup)
