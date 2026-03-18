"""
apps/core/views_analytics.py

Dua view terpisah:
  - dashboard()          : ringkas — stat cards + tabel alert saja
  - analytics_dashboard(): executive dashboard — semua chart + export PDF
"""
import json
import logging
from calendar import monthrange
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_company(request):
    company = getattr(request, 'company', None)
    if not company and getattr(request.user, 'is_superuser', False):
        from apps.core.models import Company
        company = Company.objects.first()
    return company


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD — ringkas, cepat, actionable
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def dashboard(request):
    from apps.employees.models import Employee
    from apps.attendance.models import Leave, Attendance
    from apps.contracts.models import Contract
    from apps.recruitment.models import Candidate, ManpowerRequest
    from apps.industrial.models import Violation
    from django.db.models import Count

    company = _get_company(request)
    today   = timezone.now().date()
    ctx     = {'today': today}

    if not company:
        return render(request, 'core/dashboard.html', ctx)

    # ── Stat cards ──────────────────────────────────────────────────────────
    ctx['total_karyawan']      = Employee.objects.filter(company=company, status='Aktif').count()
    ctx['karyawan_baru_bulan'] = Employee.objects.filter(
        company=company, status='Aktif',
        join_date__gte=today.replace(day=1),
    ).count()
    ctx['cuti_pending']        = Leave.objects.filter(
        employee__company=company, status='Pending').count()
    ctx['kontrak_expiring']    = Contract.objects.filter(
        employee__company=company,
        tanggal_selesai__lte=today + timedelta(days=30),
        status='Aktif',
    ).count()
    ctx['mprf_open']           = ManpowerRequest.objects.filter(
        company=company, status__in=['Open', 'In Process']).count()
    ctx['pelanggaran_pending'] = Violation.objects.filter(
        employee__company=company, status='Pending').count()

    # kandidat_proses — hitung dari company saja (tidak double count)
    rec_qs = Candidate.objects.filter(
        mprf__company=company
    ).exclude(status__in=['Hired', 'Rejected', 'Withdrawn'])
    ctx['kandidat_proses'] = rec_qs.count()

    # ── Rekap absensi hari ini (mini) ────────────────────────────────────────
    rekap_today = Attendance.objects.filter(
        employee__company=company, tanggal=today
    ).values('status').annotate(n=Count('id'))
    ctx['rekap_hari_ini'] = {r['status']: r['n'] for r in rekap_today}

    # ── Tabel alert ──────────────────────────────────────────────────────────
    ctx['leave_pending_list'] = Leave.objects.filter(
        employee__company=company, status='Pending'
    ).select_related('employee').order_by('-id')[:8]

    ctx['kontrak_alert'] = Contract.objects.filter(
        employee__company=company,
        tanggal_selesai__lte=today + timedelta(days=30),
        status='Aktif',
    ).select_related('employee').order_by('tanggal_selesai')[:8]

    ctx['recent_employees'] = Employee.objects.filter(
        company=company, status='Aktif'
    ).select_related('department', 'jabatan').order_by('-join_date', '-id')[:8]

    return render(request, 'core/dashboard.html', ctx)


# ══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS — executive dashboard, semua chart, export PDF
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def analytics_dashboard(request):
    from apps.employees.models import Employee
    from apps.attendance.models import Leave, Attendance
    from apps.contracts.models import Contract
    from apps.recruitment.models import Candidate, ManpowerRequest
    from apps.industrial.models import Violation
    from django.db.models import Count, Sum

    company = _get_company(request)
    today   = timezone.now().date()
    ctx     = {'today': today}

    if not company:
        return render(request, 'core/analytics.html', ctx)

    # ── Periode filter ───────────────────────────────────────────────────────
    # Default: bulan ini. Bisa dikembangkan dengan GET param nanti.
    bulan_start = today.replace(day=1)
    tahun_start = today.replace(month=1, day=1)

    # ── KPI ringkas untuk header analytics ──────────────────────────────────
    ctx['total_karyawan']   = Employee.objects.filter(company=company, status='Aktif').count()
    ctx['total_hadir_hari'] = Attendance.objects.filter(
        employee__company=company, tanggal=today, status='Hadir').count()
    ctx['cuti_pending']     = Leave.objects.filter(
        employee__company=company, status='Pending').count()
    ctx['kontrak_expiring'] = Contract.objects.filter(
        employee__company=company,
        tanggal_selesai__lte=today + timedelta(days=30),
        status='Aktif',
    ).count()

    # ── Chart 1: Headcount per Departemen ───────────────────────────────────
    hc_qs = Employee.objects.filter(company=company, status='Aktif') \
        .values('department__nama').annotate(n=Count('id')).order_by('-n')[:10]
    if hc_qs:
        ctx['chart_hc_labels'] = json.dumps([k['department__nama'] or 'Tanpa Dept' for k in hc_qs])
        ctx['chart_hc_data']   = json.dumps([k['n'] for k in hc_qs])

    # ── Chart 2: Komposisi Status Karyawan (PKWT/PKWTT/PHL) ─────────────────
    pkwt_qs = Employee.objects.filter(company=company, status='Aktif') \
        .values('status_karyawan').annotate(n=Count('id')).order_by('-n')
    if pkwt_qs:
        ctx['chart_pkwt_labels'] = json.dumps([k['status_karyawan'] for k in pkwt_qs])
        ctx['chart_pkwt_data']   = json.dumps([k['n'] for k in pkwt_qs])

    # ── Chart 3: Turnover per Bulan (6 bulan) ───────────────────────────────
    months6 = []
    for i in range(5, -1, -1):
        month = today.month - i
        year  = today.year
        while month <= 0:
            month += 12
            year  -= 1
        months6.append((year, month))

    turnover_labels, turnover_data = [], []
    for y, m in months6:
        last_day = monthrange(y, m)[1]
        start = today.replace(year=y, month=m, day=1)
        end   = today.replace(year=y, month=m, day=last_day)
        n_keluar = Employee.objects.filter(
            company=company,
            status__in=['Nonaktif', 'Resign', 'PHK'],
            updated_at__date__gte=start,
            updated_at__date__lte=end,
        ).count()
        turnover_labels.append(f'{m:02d}/{y}')
        turnover_data.append(n_keluar)
    ctx['chart_turnover_labels'] = json.dumps(turnover_labels)
    ctx['chart_turnover_data']   = json.dumps(turnover_data)

    # ── Chart 4: Labor Cost per Departemen ──────────────────────────────────
    lc_qs = Employee.objects.filter(company=company, status='Aktif') \
        .values('department__nama').annotate(total=Sum('gaji_pokok')).order_by('-total')[:8]
    if lc_qs:
        ctx['chart_lc_labels'] = json.dumps([k['department__nama'] or 'Tanpa Dept' for k in lc_qs])
        ctx['chart_lc_data']   = json.dumps([float(k['total'] or 0) for k in lc_qs])

    # ── Chart 5: Attendance Rate per Departemen (bulan ini) ─────────────────
    att_dept = Attendance.objects.filter(
        employee__company=company,
        tanggal__gte=bulan_start,
        tanggal__lte=today,
    ).values('employee__department__nama', 'status').annotate(n=Count('id'))

    att_map = {}
    for row in att_dept:
        dept_name = row['employee__department__nama'] or 'Tanpa Dept'
        att_map.setdefault(dept_name, {'Hadir': 0, 'total': 0})
        att_map[dept_name]['total'] += row['n']
        if row['status'] == 'Hadir':
            att_map[dept_name]['Hadir'] += row['n']

    att_labels, att_pct = [], []
    for dept_name, val in sorted(att_map.items(), key=lambda x: -x[1]['Hadir']):
        if val['total'] > 0:
            att_labels.append(dept_name)
            att_pct.append(round(val['Hadir'] / val['total'] * 100, 1))
    if att_labels:
        ctx['chart_att_labels'] = json.dumps(att_labels[:8])
        ctx['chart_att_data']   = json.dumps(att_pct[:8])

    # ── Chart 6: Trend Absensi 7 Hari ───────────────────────────────────────
    STATUS_WARNA = {
        'Hadir': '#22c55e', 'Tidak Hadir': '#ef4444',
        'Izin': '#f59e0b',  'Sakit': '#3b82f6',
        'Cuti': '#a855f7',  'WFH': '#06b6d4',
    }
    days7   = [today - timedelta(days=i) for i in range(6, -1, -1)]
    labels7 = [d.strftime('%d %b') for d in days7]

    trend_raw = Attendance.objects.filter(
        employee__company=company,
        tanggal__gte=days7[0], tanggal__lte=today,
        status__in=list(STATUS_WARNA.keys()),
    ).values('tanggal', 'status').annotate(n=Count('id'))

    trend_map = {}
    for row in trend_raw:
        trend_map.setdefault(row['status'], {})[row['tanggal']] = row['n']

    datasets = []
    for status, warna in STATUS_WARNA.items():
        if status in trend_map:
            datasets.append({
                'label': status,
                'data': [trend_map[status].get(d, 0) for d in days7],
                'borderColor': warna,
                'backgroundColor': warna + '22',
                'tension': 0.4, 'fill': False,
                'pointRadius': 4, 'borderWidth': 2,
            })
    ctx['absen_7hari_labels']   = json.dumps(labels7)
    ctx['absen_7hari_datasets'] = json.dumps(datasets)

    # ── Chart 7: Status Kontrak ──────────────────────────────────────────────
    kontrak_qs = Contract.objects.filter(employee__company=company, status='Aktif') \
        .values('tipe_kontrak').annotate(n=Count('id')).order_by('-n')
    if kontrak_qs:
        ctx['chart_contract_labels'] = json.dumps([k['tipe_kontrak'] for k in kontrak_qs])
        ctx['chart_contract_data']   = json.dumps([k['n'] for k in kontrak_qs])

    # ── Chart 8: Recruitment Pipeline ───────────────────────────────────────
    rec_qs = Candidate.objects.filter(mprf__company=company) \
        .values('status').annotate(n=Count('id'))
    rec_no_mprf = Candidate.objects.filter(mprf__isnull=True) \
        .values('status').annotate(n=Count('id'))

    rec_map = {}
    for row in rec_qs:
        rec_map[row['status']] = rec_map.get(row['status'], 0) + row['n']
    for row in rec_no_mprf:
        rec_map[row['status']] = rec_map.get(row['status'], 0) + row['n']

    STATUS_ORDER = ['Screening', 'Psikotes', 'Interview HR', 'Interview User',
                    'Medical Check', 'Offering', 'Hired', 'Rejected', 'Withdrawn']
    rec_labels = [s for s in STATUS_ORDER if s in rec_map]
    rec_data   = [rec_map[s] for s in rec_labels]
    if rec_labels:
        ctx['chart_rec_labels'] = json.dumps(rec_labels)
        ctx['chart_rec_data']   = json.dumps(rec_data)

    # ── Chart 9: Populasi per Provinsi ──────────────────────────────────────
    prov_qs = Employee.objects.filter(
        company=company, status='Aktif', provinsi__isnull=False
    ).values('provinsi__nama').annotate(n=Count('id')).order_by('-n')[:10]
    if prov_qs:
        ctx['chart_prov_labels'] = json.dumps([k['provinsi__nama'] for k in prov_qs])
        ctx['chart_prov_data']   = json.dumps([k['n'] for k in prov_qs])

    # ── Rekap absensi (untuk summary card di analytics) ─────────────────────
    def rekap(start, end):
        qs = Attendance.objects.filter(
            employee__company=company,
            tanggal__gte=start, tanggal__lte=end,
        ).values('status').annotate(n=Count('id'))
        return {r['status']: r['n'] for r in qs}

    ctx['rekap_bulan_ini'] = rekap(bulan_start, today)
    ctx['rekap_tahun_ini'] = rekap(tahun_start, today)
    ctx['company']         = company

    return render(request, 'core/analytics.html', ctx)
