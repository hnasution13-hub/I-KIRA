"""
apps/investor/views.py
"""
from decimal import Decimal
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import InvestorAccount, InvestorPool, PayoutHistory, Milestone, RevenueEntry


def _login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('investor_id'):
            return redirect('investor:login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper

def _get_investor(request):
    try:
        return InvestorAccount.objects.select_related('pool').get(
            pk=request.session['investor_id'], aktif=True)
    except InvestorAccount.DoesNotExist:
        return None


# ── Login / Logout ────────────────────────────────────────────────────────────

@require_http_methods(['GET', 'POST'])
def investor_login(request):
    if request.session.get('investor_id'):
        return redirect('investor:dashboard')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            acc = InvestorAccount.objects.get(username=username, aktif=True)
            if acc.check_password(password):
                request.session['investor_id']   = acc.pk
                request.session['investor_nama'] = acc.nama
                acc.last_login = timezone.now()
                acc.save(update_fields=['last_login'])
                return redirect('investor:dashboard')
            else:
                error = 'Username atau password salah.'
        except InvestorAccount.DoesNotExist:
            error = 'Username atau password salah.'
    return render(request, 'investor/login.html', {'error': error})


def investor_logout(request):
    request.session.flush()
    return redirect('investor:login')


# ── Dashboard ─────────────────────────────────────────────────────────────────

@_login_required
def investor_dashboard(request):
    nama = request.session.get('investor_nama', 'Investor')
    return render(request, 'investor/dashboard.html', {'nama': nama})


# ── Profil Investor ───────────────────────────────────────────────────────────

@_login_required
def investor_profil(request):
    inv = _get_investor(request)
    if not inv:
        return redirect('investor:logout')
    return render(request, 'investor/profil.html', {'nama': inv.nama})


# ── API Stats (untuk dashboard) ───────────────────────────────────────────────

@_login_required
def investor_api_stats(request):
    from apps.core.models import Company
    today = date.today()

    total_client  = Company.objects.filter(status='aktif').count()
    total_trial   = Company.objects.filter(status='trial').count()
    total_demo    = Company.objects.filter(status='demo').count()
    total_suspend = Company.objects.filter(status='suspend').count()
    client_baru   = Company.objects.filter(
        status='aktif', tanggal_daftar__year=today.year,
        tanggal_daftar__month=today.month).count()

    # ── MRR otomatis dari tenant aktif ───────────────────────────────────────
    from apps.core.models import Company as CompanyModel
    companies_aktif = CompanyModel.objects.filter(status='aktif')
    mrr_otomatis = sum(c.total_tagihan_bulanan for c in companies_aktif)
    mrr_saat_ini = Decimal(str(mrr_otomatis)) if mrr_otomatis else Decimal('0')

    # Detail per tenant untuk breakdown (tanpa expose nama jika mau disembunyikan)
    tenant_breakdown = []
    for c in companies_aktif:
        tenant_breakdown.append({
            'paket': c.get_paket_display(),
            'harga_paket': c.harga_paket,
            'harga_addon': c.harga_addon_aktif,
            'total': c.total_tagihan_bulanan,
        })

    # Histori dari RevenueEntry (tetap dipakai untuk chart historis)
    entries = list(RevenueEntry.objects.order_by('bulan')[:12])
    # Bulan ini belum ada entry? pakai kalkulasi otomatis
    revenue_chart = [{'bulan': e.bulan.strftime('%b %Y'), 'mrr': float(e.mrr)} for e in entries]
    # Tambahkan bulan ini dari kalkulasi otomatis kalau belum ada entry
    if not any(e.bulan.month == today.month and e.bulan.year == today.year for e in entries):
        revenue_chart.append({
            'bulan': today.strftime('%b %Y') + '*',
            'mrr': float(mrr_saat_ini),
        })

    proyeksi = []
    base = float(mrr_saat_ini)
    for i in range(1, 7):
        bp = (today.replace(day=1) + timedelta(days=32*i)).replace(day=1)
        proyeksi.append({'bulan': bp.strftime('%b %Y'), 'mrr': round(base * (1.3 ** i))})

    milestones = [{'judul': m.judul, 'deskripsi': m.deskripsi, 'status': m.status,
                   'status_label': m.get_status_display(),
                   'target_date': m.target_date.strftime('%b %Y') if m.target_date else None}
                  for m in Milestone.objects.all()]

    # Biaya operasional dari entry terakhir atau default
    biaya_ops = Decimal('800000')
    if entries:
        biaya_ops = entries[-1].biaya_ops
    nett = max(mrr_saat_ini - biaya_ops, Decimal('0'))

    return JsonResponse({
        'generated_at': timezone.now().isoformat(),
        'clients': {'aktif': total_client, 'trial': total_trial, 'demo': total_demo,
                    'suspend': total_suspend, 'baru_bulan_ini': client_baru},
        'revenue': {
            'mrr_saat_ini':   float(mrr_saat_ini),
            'biaya_ops':      float(biaya_ops),
            'nett':           float(nett),
            'arr_proyeksi':   float(mrr_saat_ini) * 12,
            'chart':          revenue_chart,
            'proyeksi':       proyeksi,
            'tenant_breakdown': tenant_breakdown,
            'sumber':         'otomatis',
        },
        'milestones': milestones,
        'system': {'hari_online': (today - date(2026,1,1)).days, 'versi': 'v2.0', 'status': 'Operasional'},
    })


# ── API Profil (untuk halaman profil investor) ────────────────────────────────

@_login_required
def investor_api_profil(request):
    inv = _get_investor(request)
    if not inv:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    today = date.today()

    # Revenue bulan ini — otomatis dari tenant aktif
    from apps.core.models import Company as CompanyModel
    companies_aktif = CompanyModel.objects.filter(status='aktif')
    mrr_otomatis = Decimal(str(sum(c.total_tagihan_bulanan for c in companies_aktif)))

    # Biaya operasional dari RevenueEntry terbaru atau default
    try:
        entry_terbaru = RevenueEntry.objects.latest('bulan')
        biaya_ops = entry_terbaru.biaya_ops
    except RevenueEntry.DoesNotExist:
        biaya_ops = Decimal('800000')

    nett_bulan_ini = max(mrr_otomatis - biaya_ops, Decimal('0'))

    estimasi = inv.estimasi_bulan_ini(nett_bulan_ini)

    # Riwayat payout investor ini saja
    payouts = []
    for p in PayoutHistory.objects.filter(investor=inv)[:12]:
        payouts.append({
            'bulan': p.bulan.strftime('%B %Y'),
            'jumlah': float(p.jumlah),
            'keterangan': p.keterangan,
        })

    # Daftar nama investor lain — hanya nama, tanpa nominal/persentase
    nama_investor_lain = list(
        InvestorAccount.objects.filter(aktif=True)
        .exclude(pk=inv.pk)
        .values_list('nama', flat=True)
    )

    # Simulasi perhitungan bagi hasil (transparan ke investor)
    pool = inv.pool
    simulasi = None
    if pool and nett_bulan_ini > 0:
        bagian_pool = float(nett_bulan_ini) * float(pool.persen_investor) / 100
        bagian_founder = float(nett_bulan_ini) - bagian_pool
        bagian_investor_ini = float(estimasi)
        simulasi = {
            'nett_revenue': float(nett_bulan_ini),
            'persen_investor_pool': float(pool.persen_investor),
            'bagian_semua_investor': bagian_pool,
            'bagian_founder': bagian_founder,
            'porsi_kamu': float(inv.porsi_persen),
            'bagian_kamu': bagian_investor_ini,
        }

    return JsonResponse({
        'investor': {
            'nama': inv.nama,
            'tanggal_mulai': inv.tanggal_mulai.strftime('%d %B %Y') if inv.tanggal_mulai else None,
            'modal': float(inv.modal_investasi),
            'porsi_persen': float(inv.porsi_persen),
            'total_diterima': float(inv.total_diterima),
            'target_return': float(inv.target_total_return),
            'sisa_target': float(inv.sisa_target),
            'progress_persen': inv.progress_persen,
            'status_return': inv.status_return,
            'estimasi_bulan_ini': float(estimasi),
        },
        'simulasi': simulasi,
        'payouts': payouts,
        'partner_names': nama_investor_lain,
    })
