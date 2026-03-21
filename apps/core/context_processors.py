from django.conf import settings


def global_context(request):
    """Context global tersedia di semua template."""
    context = {
        'APP_NAME':    getattr(settings, 'APP_NAME', 'i-Kira'),
        'APP_VERSION': getattr(settings, 'APP_VERSION', '1.0.0'),
        'BRAND_COLOR': getattr(settings, 'BRAND_COLOR', '#e63329'),
    }

    if not request.user.is_authenticated:
        return context

    from apps.attendance.models import Leave
    from apps.contracts.models import Contract
    from datetime import date, timedelta
    from apps.core.addon_decorators import check_addon

    company = getattr(request, 'company', None)
    is_superuser    = request.user.is_superuser
    is_developer    = getattr(request, 'is_developer', False)
    is_administrator = getattr(request, 'is_administrator', False)

    # ── Notifikasi ────────────────────────────────────────────────────────────
    if company:
        context['notif_cuti_pending'] = Leave.objects.filter(
            employee__company=company, status='Pending'
        ).count()
        context['notif_kontrak_expiring'] = Contract.objects.filter(
            employee__company=company,
            status='Aktif',
            tanggal_selesai__isnull=False,
            tanggal_selesai__lte=date.today() + timedelta(days=30),
            tanggal_selesai__gte=date.today(),
        ).count()
    else:
        context['notif_cuti_pending']     = 0
        context['notif_kontrak_expiring'] = 0

    context['current_company']    = company
    context['is_developer']       = is_developer
    context['is_administrator']   = is_administrator

    # ── Tenant switcher (superuser) ───────────────────────────────────────────
    if is_developer:
        from apps.core.models import Company as _Company
        context['all_tenants']         = _Company.objects.order_by('nama')
        context['active_tenant_id']    = request.session.get('active_tenant_id')

    # ── Add-On visibility ─────────────────────────────────────────────────────
    # Developer: semua True. Administrator & user biasa: ikut Company flags.
    context['addon_assets']              = check_addon(request, 'assets')
    context['addon_recruitment']         = check_addon(request, 'recruitment')
    context['addon_psychotest']          = check_addon(request, 'psychotest')
    context['addon_advanced_psychotest'] = check_addon(request, 'advanced_psychotest')
    context['addon_od']                  = check_addon(request, 'od')
    # Performance adalah bagian dari OD — sama nilainya
    context['addon_performance']         = context['addon_od']

    # ── License expiry warnings ───────────────────────────────────────────────
    if company and request.user.is_hr:
        try:
            from apps.core.models import AddonLicense
            from apps.core.license import WARN_DAYS, GRACE_DAYS
            from datetime import date
            today    = date.today()
            licenses = AddonLicense.objects.filter(company=company, aktif=True)
            warn_list  = []
            grace_list = []
            for lic in licenses:
                if lic.expiry is None:
                    continue
                days = (lic.expiry - today).days
                if -GRACE_DAYS <= days < 0:
                    grace_list.append({'label': lic.get_addon_display(), 'days': abs(days)})
                elif 0 <= days <= WARN_DAYS:
                    warn_list.append({'label': lic.get_addon_display(), 'days': days})
            context['license_warn_list']  = warn_list
            context['license_grace_list'] = grace_list
        except Exception:
            context['license_warn_list']  = []
            context['license_grace_list'] = []
    else:
        context['license_warn_list']  = []
        context['license_grace_list'] = []

    # ── Onboarding checklist (hanya untuk administrator/hr di company yang masih baru) ─
    if company and request.user.is_hr:
        try:
            from apps.employees.models import Employee
            from apps.core.models import Department, Position

            has_employees   = Employee.objects.filter(company=company).exists()
            has_departments = Department.objects.filter(company=company).exists()
            has_positions   = Position.objects.filter(company=company).exists()
            profile_complete = bool(company.nama and company.alamat and company.no_telp)

            onboarding_steps = [
                {
                    'key': 'profile',
                    'label': 'Lengkapi profil perusahaan',
                    'desc': 'Nama, alamat, telepon, dan logo perusahaan',
                    'done': profile_complete,
                    'url': 'company_profile',
                    'icon': 'building',
                },
                {
                    'key': 'department',
                    'label': 'Tambah departemen',
                    'desc': 'Buat minimal satu departemen terlebih dahulu',
                    'done': has_departments,
                    'url': 'job_library_list',
                    'icon': 'layer-group',
                },
                {
                    'key': 'position',
                    'label': 'Tambah jabatan',
                    'desc': 'Buat struktur jabatan sesuai organisasi',
                    'done': has_positions,
                    'url': 'job_library_list',
                    'icon': 'sitemap',
                },
                {
                    'key': 'employee',
                    'label': 'Input data karyawan pertama',
                    'desc': 'Tambah atau impor data karyawan',
                    'done': has_employees,
                    'url': 'employee_add',
                    'icon': 'user-plus',
                },
            ]

            done_count = sum(1 for s in onboarding_steps if s['done'])
            all_done   = done_count == len(onboarding_steps)

            # Tampilkan selama belum semua selesai
            context['onboarding_steps']    = onboarding_steps
            context['onboarding_done']     = done_count
            context['onboarding_total']    = len(onboarding_steps)
            context['onboarding_all_done'] = all_done
            context['show_onboarding']     = not all_done
        except Exception:
            context['show_onboarding'] = False
    else:
        context['show_onboarding'] = False

    return context
