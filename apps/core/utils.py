"""
Utility helpers untuk multi-tenant i-Kira.
"""


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
