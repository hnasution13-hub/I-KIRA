# ==================================================
# FILE: apps/reports/views.py
# PERBAIKAN: Tambah export Excel & PDF, perbaiki semua view
# VERSION: 1.0.2
# ==================================================

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.core.addon_decorators import addon_required
from django.http import HttpResponse
from apps.assets.models import Asset
from apps.employees.models import Employee
from apps.maintenance.models import Maintenance
from apps.movements.models import Movement, Assignment
from apps.audit.models import AuditLog
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .export import export_assets_excel, export_assets_pdf, export_depreciation_excel


def _get_company(request):
    """Helper multi-tenant — fallback ke Company.objects.first() untuk superuser."""
    from apps.core.models import Company
    company = getattr(request, 'company', None)
    if not company and getattr(request.user, 'is_superuser', False):
        company = Company.objects.first()
    return company


@login_required
@addon_required('assets')
def dashboard_view(request):
    company = _get_company(request)
    asset_qs = Asset.objects.filter(company=company) if company else Asset.objects.all()

    total_assets = asset_qs.count()
    total_employees = Employee.objects.filter(company=company).count() if company else Employee.objects.count()
    active_maintenance = Maintenance.objects.filter(
        asset__company=company, status__in=['Scheduled', 'In Progress']
    ).count() if company else Maintenance.objects.filter(status__in=['Scheduled', 'In Progress']).count()
    total_movements = Movement.objects.filter(asset__company=company).count() if company else Movement.objects.count()

    # Asset by condition
    baik         = asset_qs.filter(condition='Baik').count()
    rusak_ringan = asset_qs.filter(condition='Rusak Ringan').count()
    rusak_berat  = asset_qs.filter(condition='Rusak Berat').count()
    perbaikan    = asset_qs.filter(condition='Dalam Perbaikan').count()

    # Asset by status
    active_count      = asset_qs.filter(status='ACTIVE').count()
    maintenance_count = asset_qs.filter(status='MAINTENANCE').count()
    retired_count     = asset_qs.filter(status='RETIRED').count()
    broken_count      = asset_qs.filter(status='BROKEN').count()

    # Total nilai aset
    total_nilai = asset_qs.aggregate(total=Sum('purchase_price'))['total'] or 0

    # Recent activities
    recent_logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:10]

    # Top categories
    categories_data = asset_qs.values('category__name').annotate(
        total=Count('id')
    ).order_by('-total')[:5]

    # Recent movements
    mv_qs = Movement.objects.select_related('asset', 'from_pic', 'to_pic')
    if company:
        mv_qs = mv_qs.filter(asset__company=company)
    recent_movements = mv_qs.order_by('-movement_date')[:5]

    # Upcoming maintenance
    maint_qs = Maintenance.objects.filter(status='Scheduled').select_related('asset')
    if company:
        maint_qs = maint_qs.filter(asset__company=company)
    upcoming_maintenance = maint_qs.order_by('maintenance_date')[:5]

    context = {
        'total_assets': total_assets,
        'total_employees': total_employees,
        'active_maintenance': active_maintenance,
        'total_movements': total_movements,
        'total_nilai': total_nilai,
        'active_count': active_count,
        'maintenance_count': maintenance_count,
        'retired_count': retired_count,
        'broken_count': broken_count,
        'baik': baik,
        'rusak_ringan': rusak_ringan,
        'rusak_berat': rusak_berat,
        'perbaikan': perbaikan,
        'recent_logs': recent_logs,
        'categories_data': categories_data,
        'recent_movements': recent_movements,
        'upcoming_maintenance': upcoming_maintenance,
    }
    return render(request, 'asset_reports/dashboard.html', context)


@login_required
@addon_required('assets')
def pic_beban_view(request):
    company = _get_company(request)
    emp_qs = Employee.objects.filter(
        current_assignments__isnull=False
    ).annotate(
        total_asset=Count('current_assignments'),
        total_nilai=Sum('current_assignments__asset__purchase_price')
    ).order_by('-total_asset')
    if company:
        emp_qs = emp_qs.filter(company=company)
    context = {'employees': emp_qs}
    return render(request, 'asset_reports/pic_beban.html', context)


@login_required
@addon_required('assets')
def stock_opname_view(request):
    company = _get_company(request)
    assets = Asset.objects.select_related(
        'responsible', 'location', 'category'
    ).order_by('asset_code')
    if company:
        assets = assets.filter(company=company)

    # Export Excel
    if request.GET.get('export') == 'excel':
        output = export_assets_excel(assets)
        if output:
            filename = f"stock_opname_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

    # Export PDF
    if request.GET.get('export') == 'pdf':
        output = export_assets_pdf(assets)
        if output:
            filename = f"stock_opname_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            response = HttpResponse(output.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

    context = {'assets': assets}
    return render(request, 'asset_reports/stock_opname.html', context)


@login_required
@addon_required('assets')
def asset_card_view(request, asset_id):
    company = _get_company(request)
    qs = Asset.objects.filter(company=company) if company else Asset.objects.all()
    asset = get_object_or_404(qs, pk=asset_id)
    movements = Movement.objects.filter(asset=asset).order_by('movement_date', 'created_at')
    maintenances = Maintenance.objects.filter(asset=asset).order_by('-maintenance_date')
    context = {
        'asset': asset,
        'movements': movements,
        'maintenances': maintenances,
    }
    return render(request, 'asset_reports/asset_card.html', context)


@login_required
@addon_required('assets')
def asset_card_print(request, asset_id):
    company = _get_company(request)
    qs = Asset.objects.filter(company=company) if company else Asset.objects.all()
    asset = get_object_or_404(qs, pk=asset_id)
    movements = Movement.objects.filter(asset=asset).order_by('movement_date', 'created_at')
    maintenances = Maintenance.objects.filter(asset=asset).order_by('-maintenance_date')
    depreciations = asset.depreciation_set.all().order_by('year') if hasattr(asset, 'depreciation_set') else []
    context = {
        'asset'        : asset,
        'movements'    : movements,
        'maintenances' : maintenances,
        'depreciations': depreciations,
        'company'      : company,
    }
    return render(request, 'asset_reports/asset_card_print.html', context)


@login_required
@addon_required('assets')
def depreciation_report_view(request):
    company = _get_company(request)
    assets = Asset.objects.prefetch_related('depreciation_set').select_related('category')
    if company:
        assets = assets.filter(company=company)

    if request.GET.get('export') == 'excel':
        output = export_depreciation_excel(assets)
        if output:
            filename = f"laporan_depresiasi_{timezone.now().strftime('%Y%m%d')}.xlsx"
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

    context = {'assets': assets}
    return render(request, 'asset_reports/depreciation_report.html', context)


@login_required
@addon_required('assets')
def maintenance_report_view(request):
    company = _get_company(request)
    maintenances = Maintenance.objects.select_related('asset')
    if company:
        maintenances = maintenances.filter(asset__company=company)

    if request.GET.get('export') == 'excel':
        try:
            import openpyxl
            import io
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Laporan Maintenance"
            headers = ['No', 'Aset', 'Tipe', 'Tanggal', 'Teknisi', 'Biaya', 'Status', 'Keterangan']
            ws.append(headers)
            for idx, m in enumerate(maintenances, 1):
                ws.append([
                    idx, str(m.asset), m.maintenance_type,
                    m.maintenance_date.strftime('%d/%m/%Y'),
                    m.technician or '-', float(m.cost), m.status, m.description or '-'
                ])
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            filename = f"laporan_maintenance_{timezone.now().strftime('%Y%m%d')}.xlsx"
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception:
            pass

    context = {'maintenances': maintenances}
    return render(request, 'asset_reports/maintenance_report.html', context)