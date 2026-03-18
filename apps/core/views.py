from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Department, Position, User, Company, OrgChart, ApprovalMatrix
from .addon_decorators import check_addon


def _get_company(request):
    """
    Ambil company dari request. Untuk superuser (developer) yang company=None,
    fallback ke Company pertama agar tidak IntegrityError NOT NULL.
    """
    company = getattr(request, 'company', None)
    if not company and getattr(request.user, 'is_superuser', False):
        company = Company.objects.first()
    return company


# ══════════════════════════════════════════════════════════════════════════════
#  LANDING & AUTH
# ══════════════════════════════════════════════════════════════════════════════

def landing_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def login_view(request):
    from django.contrib.auth import authenticate, login
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Username atau password salah.')
    return render(request, 'auth/login.html')


def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')


# ══════════════════════════════════════════════════════════════════════════════
#  DECORATOR HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _hr_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_hr or request.user.is_staff):
            messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name  = request.POST.get('last_name',  user.last_name).strip()
        user.email      = request.POST.get('email',      user.email).strip()
        if hasattr(user, 'no_hp'):
            user.no_hp  = request.POST.get('no_hp', '').strip()
        if 'foto' in request.FILES:
            # Hapus foto lama jika ada
            if user.foto:
                import os
                if os.path.isfile(user.foto.path):
                    os.remove(user.foto.path)
            user.foto = request.FILES['foto']
        user.save()
        messages.success(request, 'Profil berhasil diperbarui.')
    return render(request, 'core/profile.html')


@login_required
def company_profile(request):
    if not request.user.is_hr:
        return redirect('dashboard')
    company = _get_company(request)
    if request.method == 'POST' and company:
        company.nama  = request.POST.get('nama', company.nama)
        company.email = request.POST.get('email', company.email)
        company.save()
        messages.success(request, 'Profil perusahaan berhasil diperbarui.')
    return render(request, 'core/company_profile.html', {'company': company})


@login_required
def change_password(request):
    from django.contrib.auth import update_session_auth_hash
    if request.method == 'POST':
        old = request.POST.get('old_password')
        new = request.POST.get('new_password')
        if request.user.check_password(old):
            request.user.set_password(new)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password berhasil diubah.')
        else:
            messages.error(request, 'Password lama salah.')
    return render(request, 'core/profile.html')


# ══════════════════════════════════════════════════════════════════════════════
#  JOB LIBRARY
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def job_library_list(request):
    company      = _get_company(request)
    q            = request.GET.get('q', '').strip()
    dept_filter  = request.GET.get('dept', '').strip()
    level_filter = request.GET.get('level', '').strip()

    positions = Position.objects.filter(company=company, aktif=True).select_related('department', 'parent')

    if q:
        positions = positions.filter(nama__icontains=q)
    if dept_filter:
        positions = positions.filter(department_id=dept_filter)
    if level_filter:
        positions = positions.filter(level=level_filter)

    positions    = positions.order_by('department__nama', 'level', 'nama')
    departments  = Department.objects.filter(company=company, aktif=True).order_by('nama')

    return render(request, 'core/job_library_list.html', {
        'positions':     positions,
        'departments':   departments,
        'level_choices': Position.LEVEL_CHOICES,
        'q':             q,
        'dept_filter':   dept_filter,
        'level_filter':  level_filter,
    })


@login_required
@_hr_required
def job_library_form(request, pk=None):
    company = _get_company(request)
    instance = get_object_or_404(Position, pk=pk, company=company) if pk else None
    departments = Department.objects.filter(company=company, aktif=True)
    positions_for_parent = Position.objects.filter(company=company, aktif=True)
    if pk:
        positions_for_parent = positions_for_parent.exclude(pk=pk)

    if request.method == 'POST':
        parent_id = request.POST.get('parent') or None
        dept_id   = request.POST.get('department') or None
        data = {
            'company':           company,
            'nama':              request.POST.get('nama', '').strip(),
            'level':             request.POST.get('level', 'Staff'),
            'department_id':     dept_id,
            'parent_id':         parent_id,
            'deskripsi':         request.POST.get('deskripsi', ''),
            'job_desc':          request.POST.get('job_desc', ''),
            'skill_wajib':       request.POST.get('skill_wajib', ''),
            'skill_diinginkan':  request.POST.get('skill_diinginkan', ''),
            'pendidikan_min':    request.POST.get('pendidikan_min', ''),
            'pengalaman_min':    int(request.POST.get('pengalaman_min', 0)),
            'bobot_skill_wajib':    int(request.POST.get('bobot_skill_wajib', 40)),
            'bobot_pengalaman':     int(request.POST.get('bobot_pengalaman', 25)),
            'bobot_pendidikan':     int(request.POST.get('bobot_pendidikan', 20)),
            'bobot_skill_tambahan': int(request.POST.get('bobot_skill_tambahan', 15)),
        }
        if not data['nama']:
            messages.error(request, 'Nama jabatan wajib diisi.')
            return render(request, 'core/job_library_form.html', {
                'instance': instance, 'departments': departments,
                'positions_for_parent': positions_for_parent,
                'level_choices': Position.LEVEL_CHOICES,
            })

        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()
            messages.success(request, 'Jabatan berhasil diperbarui.')
        else:
            from django.db import IntegrityError
            try:
                Position.objects.create(**data)
                messages.success(request, 'Jabatan berhasil ditambahkan.')
            except IntegrityError:
                messages.error(request, f'Jabatan "{data["nama"]}" sudah ada di perusahaan ini.')
                return render(request, 'core/job_library_form.html', {
                    'instance': instance,
                    'departments': departments,
                    'positions_for_parent': positions_for_parent,
                    'level_choices': Position.LEVEL_CHOICES,
                })
        return redirect('job_library_list')

    ctx = {
        'instance': instance,
        'departments': departments,
        'positions_for_parent': positions_for_parent,
        'level_choices': Position.LEVEL_CHOICES,
    }
    return render(request, 'core/job_library_form.html', ctx)


@login_required
def job_library_detail(request, pk):
    company = _get_company(request)
    position = get_object_or_404(Position, pk=pk, company=company)
    chain = position.get_full_approval_chain('leave')
    ctx = {
        'position': position,
        'ancestors': position.get_ancestors(),
        'descendants': position.get_descendants(),
        'approval_chain': chain,
    }
    return render(request, 'core/job_library_detail.html', ctx)


@login_required
@_hr_required
def job_library_delete(request, pk):
    company = _get_company(request)
    position = get_object_or_404(Position, pk=pk, company=company)
    if request.method == 'POST':
        position.aktif = False
        position.save(update_fields=['aktif'])
        messages.success(request, f'Jabatan "{position.nama}" dinonaktifkan.')
        return redirect('job_library_list')
    return render(request, 'core/job_library_confirm_delete.html', {'position': position})


# ══════════════════════════════════════════════════════════════════════════════
#  ORG CHART
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def orgchart_list(request):
    company = _get_company(request)
    if not company and request.user.is_superuser:
        from apps.core.models import Company
        company = Company.objects.first()
    charts = OrgChart.objects.filter(company=company).order_by('-berlaku_mulai')
    return render(request, 'core/orgchart_list.html', {'charts': charts})


@login_required
def orgchart_detail(request, pk):
    """Render org chart visual per departemen."""
    company = _get_company(request)
    if not company and request.user.is_superuser:
        from apps.core.models import Company
        company = Company.objects.first()
    chart = get_object_or_404(OrgChart, pk=pk, company=company)
    tree  = chart.get_tree_by_department()
    ctx = {
        'chart': chart,
        'tree':  tree,
    }
    return render(request, 'core/orgchart_detail.html', ctx)


@login_required
def orgchart_json(request, pk):
    """JSON endpoint — dipakai JS renderer untuk menampilkan tree interaktif."""
    from django.core.cache import cache

    company = _get_company(request)
    if not company and request.user.is_superuser:
        from apps.core.models import Company
        company = Company.objects.first()
    chart = get_object_or_404(OrgChart, pk=pk, company=company)

    # Cache key unik per chart & company
    cache_key = f'orgchart_json_{pk}_{company.id if company else 0}'
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    positions = Position.objects.filter(
        company=company, aktif=True,
    ).select_related('department', 'parent').order_by('department__nama', 'level', 'nama')

    from apps.employees.models import Employee
    emp_by_jabatan = {}
    for emp in Employee.objects.filter(company=company, status='Aktif').only('id', 'nama', 'nik', 'jabatan_id'):
        emp_by_jabatan.setdefault(emp.jabatan_id, []).append({
            'id':   emp.id,
            'nama': emp.nama,
            'nik':  emp.nik,
        })

    nodes = []
    for pos in positions:
        nodes.append({
            'id':          pos.id,
            'nama':        pos.nama,
            'level':       pos.level,
            'department':  pos.department.nama if pos.department else None,
            'parent_id':   pos.parent_id,
            'employees':   emp_by_jabatan.get(pos.id, []),
            'emp_count':   len(emp_by_jabatan.get(pos.id, [])),
        })

    data = {'chart_id': chart.id, 'chart_nama': chart.nama, 'nodes': nodes}

    # Simpan cache selama 5 menit
    cache.set(cache_key, data, timeout=300)

    return JsonResponse(data)


@login_required
@_hr_required
def orgchart_create(request):
    from apps.core.models import Company
    company = _get_company(request)
    # Superuser (developer) tidak punya company — fallback ke company pertama
    if not company and request.user.is_superuser:
        company = Company.objects.first()
    if request.method == 'POST':
        from django.utils.dateparse import parse_date
        OrgChart.objects.create(
            company=company,
            nama=request.POST['nama'],
            periode=request.POST.get('periode', ''),
            berlaku_mulai=parse_date(request.POST['berlaku_mulai']),
            berlaku_sampai=parse_date(request.POST.get('berlaku_sampai', '') or '') or None,
            status=request.POST.get('status', 'draft'),
            deskripsi=request.POST.get('deskripsi', ''),
            created_by=request.user,
        )
        messages.success(request, 'Org chart berhasil dibuat.')
        return redirect('orgchart_list')
    return render(request, 'core/orgchart_form.html')


@login_required
@_hr_required
def orgchart_activate(request, pk):
    """Aktifkan org chart, arsipkan yang lain."""
    company = _get_company(request)
    chart   = get_object_or_404(OrgChart, pk=pk, company=company)
    if request.method == 'POST':
        OrgChart.objects.filter(company=company, status='aktif').update(status='arsip')
        chart.status = 'aktif'
        chart.save(update_fields=['status'])
        messages.success(request, f'Org chart "{chart.nama}" diaktifkan.')
    return redirect('orgchart_detail', pk=pk)


# ══════════════════════════════════════════════════════════════════════════════
#  APPROVAL MATRIX
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@_hr_required
def approval_matrix_list(request):
    company = _get_company(request)
    matrices = ApprovalMatrix.objects.filter(
        company=company,
    ).select_related('jabatan_pemohon', 'jabatan_approver').order_by('modul', 'jabatan_pemohon')

    # Group by modul untuk tampilan tabel
    from itertools import groupby
    grouped = {}
    for m in matrices:
        grouped.setdefault(m.get_modul_display(), []).append(m)

    ctx = {
        'matrices': matrices,
        'grouped':  grouped,
        'modul_choices': ApprovalMatrix.MODUL_CHOICES,
    }
    return render(request, 'core/approval_matrix_list.html', ctx)


@login_required
@_hr_required
def approval_matrix_form(request, pk=None):
    company = _get_company(request)
    instance = get_object_or_404(ApprovalMatrix, pk=pk, company=company) if pk else None
    positions = Position.objects.filter(company=company, aktif=True).select_related('department')

    if request.method == 'POST':
        data = {
            'company':           company,
            'modul':             request.POST['modul'],
            'jabatan_pemohon_id': request.POST['jabatan_pemohon'],
            'level_approval':    int(request.POST.get('level_approval', 1)),
            'jabatan_approver_id': request.POST.get('jabatan_approver') or None,
            'auto_approve_hari': int(request.POST.get('auto_approve_hari', 0)),
            'notif_email':       'notif_email' in request.POST,
            'aktif':             'aktif' in request.POST,
        }
        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()
            messages.success(request, 'Approval matrix diperbarui.')
        else:
            ApprovalMatrix.objects.update_or_create(
                company=company,
                modul=data['modul'],
                jabatan_pemohon_id=data['jabatan_pemohon_id'],
                level_approval=data['level_approval'],
                defaults={k: v for k, v in data.items()
                          if k not in ('company', 'modul', 'jabatan_pemohon_id', 'level_approval')},
            )
            messages.success(request, 'Approval matrix ditambahkan.')
        return redirect('approval_matrix_list')

    ctx = {
        'instance': instance,
        'positions': positions,
        'modul_choices': ApprovalMatrix.MODUL_CHOICES,
    }
    return render(request, 'core/approval_matrix_form.html', ctx)


@login_required
@_hr_required
def approval_matrix_delete(request, pk):
    company = _get_company(request)
    instance = get_object_or_404(ApprovalMatrix, pk=pk, company=company)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, 'Approval matrix dihapus.')
        return redirect('approval_matrix_list')
    return render(request, 'core/approval_matrix_confirm_delete.html', {'instance': instance})


# ══════════════════════════════════════════════════════════════════════════════
#  API ENDPOINTS (AJAX)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def api_position_detail(request, pk):
    company = _get_company(request)
    position = get_object_or_404(Position, pk=pk, company=company)
    return JsonResponse({
        'id':         position.id,
        'nama':       position.nama,
        'level':      position.level,
        'department': position.department.nama if position.department else '',
        'parent_id':  position.parent_id,
        'parent_nama': position.parent.nama if position.parent else '',
    })


@login_required
def api_positions_list(request):
    company = _get_company(request)
    dept_id   = request.GET.get('department')
    qs        = Position.objects.filter(company=company, aktif=True).select_related('department')
    if dept_id:
        qs = qs.filter(department_id=dept_id)
    data = [{'id': p.id, 'nama': p.nama, 'level': p.level} for p in qs]
    return JsonResponse({'positions': data})


@login_required
@_hr_required
def api_position_update_parent(request, pk):
    """AJAX POST — update parent_id jabatan (untuk drag & drop org chart)."""
    import json
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    company  = _get_company(request)
    position = get_object_or_404(Position, pk=pk, company=company)
    try:
        body      = json.loads(request.body)
        parent_id = body.get('parent_id')   # None = puncak hierarki
        if parent_id:
            parent = get_object_or_404(Position, pk=parent_id, company=company)
            # Cegah circular — pastikan parent bukan descendant dari position ini
            ancestors = set()
            cur = parent
            while cur:
                if cur.pk == position.pk:
                    return JsonResponse({'error': 'Circular hierarchy detected'}, status=400)
                ancestors.add(cur.pk)
                cur = cur.parent
            position.parent_id = parent_id
        else:
            position.parent_id = None
        position.save(update_fields=['parent_id'])
        return JsonResponse({'ok': True, 'id': position.pk, 'parent_id': position.parent_id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@_hr_required
def api_position_update_parent(request, pk):
    """AJAX POST — update parent_id jabatan (drag & drop org chart)."""
    import json
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    company  = _get_company(request)
    if not company and request.user.is_superuser:
        from apps.core.models import Company as Co
        company = Co.objects.first()
    position = get_object_or_404(Position, pk=pk, company=company)
    try:
        body      = json.loads(request.body)
        parent_id = body.get('parent_id')  # None = puncak hierarki

        # Cek ApprovalMatrix eksplisit yang dimiliki jabatan ini
        matrix_count = ApprovalMatrix.objects.filter(
            jabatan_pemohon=position, aktif=True
        ).count()

        if parent_id:
            parent = get_object_or_404(Position, pk=parent_id, company=company)
            # Cegah circular hierarchy
            cur = parent
            while cur:
                if cur.pk == position.pk:
                    return JsonResponse({'error': 'Circular hierarchy — jabatan tidak bisa jadi atasan dirinya sendiri.'}, status=400)
                cur = cur.parent
            position.parent_id = parent_id
        else:
            position.parent_id = None

        position.save(update_fields=['parent_id'])
        return JsonResponse({
            'ok':           True,
            'id':           position.pk,
            'parent_id':    position.parent_id,
            'matrix_count': matrix_count,  # Frontend pakai ini untuk tampilkan warning
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_approval_chain(request):
    """AJAX: kembalikan approval chain untuk jabatan + modul tertentu."""
    from utils.approval_engine import get_approval_chain_display
    company = _get_company(request)
    jabatan_id   = request.GET.get('jabatan_id')
    modul        = request.GET.get('modul', 'leave')

    if not jabatan_id:
        return JsonResponse({'chain': []})

    jabatan = get_object_or_404(Position, pk=jabatan_id, company=company)

    # Buat dummy employee object untuk helper
    _company = _get_company(request)
    _jabatan = jabatan

    class _FakeEmp:
        company = _company
        jabatan = _jabatan

    chain = get_approval_chain_display(_FakeEmp(), modul)
    return JsonResponse({'chain': chain})


# ─── Tenant Switcher (superuser only) ────────────────────────────────────────

@login_required
def switch_tenant(request):
    """Switch tenant aktif untuk superuser — disimpan di session."""
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    company_id = request.POST.get('company_id') or request.GET.get('company_id')

    if company_id == '0' or not company_id:
        # Reset — lihat semua (no active tenant)
        request.session.pop('active_tenant_id', None)
    else:
        try:
            company = Company.objects.get(pk=company_id)
            request.session['active_tenant_id'] = company.pk
        except Company.DoesNotExist:
            request.session.pop('active_tenant_id', None)

    # Redirect ke halaman sebelumnya, fallback ke dashboard
    next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
    if next_url.startswith('/'):
        return redirect(next_url)
    return redirect(next_url)


# ─── Tenant List (superuser only) ────────────────────────────────────────────

@login_required
def tenant_list(request):
    """Daftar semua company/tenant — hanya bisa diakses superuser (developer)."""
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    from apps.employees.models import Employee
    from apps.attendance.models import Attendance

    companies = Company.objects.order_by('nama')
    data = []
    for c in companies:
        emp_aktif = Employee.objects.filter(company=c, status='Aktif').count()
        emp_total = Employee.objects.filter(company=c).count()
        n_abs     = Attendance.objects.filter(employee__company=c).count()
        data.append({
            'company':    c,
            'emp_aktif':  emp_aktif,
            'emp_total':  emp_total,
            'n_absensi':  n_abs,
        })

    return render(request, 'core/tenant_list.html', {
        'data':    data,
        'total':   companies.count(),
    })


# ─── Custom Error Handlers ────────────────────────────────────────────────────

def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    return render(request, 'errors/500.html', status=500)