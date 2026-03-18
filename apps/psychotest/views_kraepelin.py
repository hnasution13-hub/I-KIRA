"""
apps/psychotest/views_kraepelin.py

Kraepelin Test Engine:
  - kraepelin_create          : HR buat sesi (kandidat atau karyawan)
  - kraepelin_intro           : halaman intro sebelum tes (public)
  - kraepelin_tes             : halaman tes fullscreen (public)
  - kraepelin_submit_baris    : AJAX submit jawaban per baris
  - kraepelin_selesai         : halaman hasil setelah tes
  - kraepelin_result_hr       : HR lihat hasil detail
  - _generate_kolom           : helper generate deret angka dari seed
  - _hitung_kraepelin         : helper scoring otomatis
"""
import json
import random
import logging
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.core.addon_decorators import addon_required
from .models import KraepelinSession, KraepelinRowResult, KraepelinResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: GENERATE DERET ANGKA
# ─────────────────────────────────────────────────────────────────────────────

def _generate_kolom(seed: int, jumlah_baris: int, digit_per_baris: int) -> list[list[int]]:
    """
    Generate deret angka Kraepelin.
    Return: list of list — kolom[baris][digit] berisi angka 1-9.
    Reproducible dari seed yang sama.
    """
    rng = random.Random(seed)
    return [
        [rng.randint(1, 9) for _ in range(digit_per_baris + 1)]
        for _ in range(jumlah_baris)
    ]


def _kunci_baris(kolom_baris: list[int]) -> list[int]:
    """
    Hitung kunci jawaban untuk satu baris.
    Jawaban[i] = (kolom[i] + kolom[i+1]) % 10
    """
    return [(kolom_baris[i] + kolom_baris[i + 1]) % 10
            for i in range(len(kolom_baris) - 1)]


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: SCORING
# ─────────────────────────────────────────────────────────────────────────────

def _hitung_kraepelin(session: KraepelinSession) -> KraepelinResult:
    """Hitung semua skor dan simpan KraepelinResult."""
    rows = list(session.row_results.order_by('baris'))

    if not rows:
        result, _ = KraepelinResult.objects.update_or_create(
            session=session,
            defaults={
                'candidate': session.candidate,
                'employee':  session.employee,
                'skor_total': 0, 'grade': 'D',
            }
        )
        return result

    kecepatan_list = [r.dikerjakan for r in rows]   # kolom dikerjakan per baris
    benar_list     = [r.benar for r in rows]
    salah_list     = [r.salah for r in rows]
    total_dikerjakan = sum(kecepatan_list)
    total_benar      = sum(benar_list)

    # ── Kecepatan: rata-rata kolom dikerjakan per baris
    mean_kecepatan = total_dikerjakan / len(rows) if rows else 0

    # ── Ketelitian: % benar dari yang dikerjakan
    ketelitian = (total_benar / total_dikerjakan * 100) if total_dikerjakan > 0 else 0

    # ── Konsistensi: 100 - (std_dev / mean * 100), makin kecil std_dev makin konsisten
    if len(kecepatan_list) > 1 and mean_kecepatan > 0:
        variance = sum((x - mean_kecepatan) ** 2 for x in kecepatan_list) / len(kecepatan_list)
        std_dev  = variance ** 0.5
        konsistensi = max(0, 100 - (std_dev / mean_kecepatan * 100))
    else:
        konsistensi = 100.0

    # ── Ketahanan: bandingkan kecepatan paruh akhir vs awal
    mid = len(rows) // 2
    awal  = kecepatan_list[:mid]
    akhir = kecepatan_list[mid:]
    mean_awal  = sum(awal)  / len(awal)  if awal  else 0
    mean_akhir = sum(akhir) / len(akhir) if akhir else 0
    if mean_awal > 0:
        ketahanan = min(100, mean_akhir / mean_awal * 100)
    else:
        ketahanan = 100.0

    # ── Skor total: bobot kecepatan 30%, ketelitian 40%, konsistensi 20%, ketahanan 10%
    # Normalisasi kecepatan ke 0-100 (asumsi target = digit_per_baris, max feasible ~80%)
    target_kecepatan = session.digit_per_baris * 0.8
    norm_kecepatan = min(100, mean_kecepatan / target_kecepatan * 100) if target_kecepatan > 0 else 0

    skor_total = round(
        norm_kecepatan * 0.30 +
        ketelitian     * 0.40 +
        konsistensi    * 0.20 +
        ketahanan      * 0.10
    )

    grade = 'A' if skor_total >= 80 else 'B' if skor_total >= 65 else 'C' if skor_total >= 50 else 'D'

    detail = {
        'kecepatan_per_baris': kecepatan_list,
        'benar_per_baris':     benar_list,
        'salah_per_baris':     salah_list,
        'mean_kecepatan':      round(mean_kecepatan, 2),
        'ketelitian':          round(ketelitian, 2),
        'konsistensi':         round(konsistensi, 2),
        'ketahanan':           round(ketahanan, 2),
        'total_dikerjakan':    total_dikerjakan,
        'total_benar':         total_benar,
    }

    result, _ = KraepelinResult.objects.update_or_create(
        session=session,
        defaults={
            'candidate':        session.candidate,
            'employee':         session.employee,
            'skor_kecepatan':   round(norm_kecepatan, 2),
            'skor_ketelitian':  round(ketelitian, 2),
            'skor_konsistensi': round(konsistensi, 2),
            'skor_ketahanan':   round(ketahanan, 2),
            'skor_total':       skor_total,
            'grade':            grade,
            'detail':           detail,
        }
    )

    # Update status session
    session.status       = 'completed'
    session.completed_at = timezone.now()
    session.save(update_fields=['status', 'completed_at'])

    return result


# ─────────────────────────────────────────────────────────────────────────────
# HR — BUAT SESI KRAEPELIN
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@addon_required('psychotest')
def kraepelin_create(request, candidate_pk=None, employee_pk=None):
    """HR buat sesi Kraepelin untuk kandidat atau karyawan."""
    from apps.recruitment.models import Candidate
    from apps.employees.models import Employee

    candidate = get_object_or_404(Candidate, pk=candidate_pk) if candidate_pk else None
    employee  = get_object_or_404(Employee,  pk=employee_pk)  if employee_pk  else None

    if not candidate and not employee:
        messages.error(request, 'Kandidat atau karyawan tidak ditemukan.')
        return redirect('dashboard')

    company = getattr(request, 'company', None)
    if not company and request.user.is_superuser:
        from apps.core.models import Company
        company = Company.objects.first()

    if request.method == 'POST':
        tujuan          = request.POST.get('tujuan', 'rekrutmen')
        jumlah_baris    = int(request.POST.get('jumlah_baris', 50))
        digit_per_baris = int(request.POST.get('digit_per_baris', 60))
        detik_per_baris = int(request.POST.get('detik_per_baris', 30))
        expired_days    = int(request.POST.get('expired_days', 7))

        # Seed unik per sesi
        seed = random.randint(1, 2**30)

        sesi = KraepelinSession.objects.create(
            company         = company,
            candidate       = candidate,
            employee        = employee,
            tujuan          = tujuan,
            jumlah_baris    = jumlah_baris,
            digit_per_baris = digit_per_baris,
            detik_per_baris = detik_per_baris,
            seed            = seed,
            expired_at      = timezone.now() + timedelta(days=expired_days),
            created_by      = request.user.get_full_name() or request.user.username,
        )

        link_full = request.build_absolute_uri(f'/psychotest/kraepelin/{sesi.token}/')
        messages.success(request, f'Sesi Kraepelin berhasil dibuat. Link: {link_full}')

        if candidate:
            return redirect('candidate_detail', pk=candidate_pk)
        return redirect('employee_detail', pk=employee_pk)

    return render(request, 'psychotest/kraepelin_create.html', {
        'candidate': candidate,
        'employee':  employee,
    })


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC — INTRO & TES
# ─────────────────────────────────────────────────────────────────────────────

def kraepelin_intro(request, token):
    """Halaman intro sebelum tes dimulai."""
    sesi = get_object_or_404(KraepelinSession, token=token)

    if sesi.status == 'completed':
        return redirect('kraepelin_selesai', token=token)
    if sesi.is_expired:
        return render(request, 'psychotest/kraepelin_expired.html', {'sesi': sesi})

    peserta_nama = sesi.get_peserta_nama()
    return render(request, 'psychotest/kraepelin_intro.html', {
        'sesi':         sesi,
        'peserta_nama': peserta_nama,
        'total_waktu':  sesi.jumlah_baris * sesi.detik_per_baris,
    })


def kraepelin_tes(request, token):
    """Halaman tes fullscreen — public tanpa login."""
    sesi = get_object_or_404(KraepelinSession, token=token)

    if sesi.status == 'completed':
        return redirect('kraepelin_selesai', token=token)
    if sesi.is_expired:
        return render(request, 'psychotest/kraepelin_expired.html', {'sesi': sesi})

    # Mark started
    if sesi.status == 'pending':
        sesi.status     = 'started'
        sesi.started_at = timezone.now()
        sesi.save(update_fields=['status', 'started_at'])

    # Generate semua baris — kirim ke template sebagai JSON
    kolom = _generate_kolom(sesi.seed, sesi.jumlah_baris, sesi.digit_per_baris)

    # Cek baris yang sudah dikerjakan (untuk resume)
    selesai_baris = set(
        sesi.row_results.values_list('baris', flat=True)
    )
    baris_mulai = max(selesai_baris) + 1 if selesai_baris else 1

    return render(request, 'psychotest/kraepelin_tes.html', {
        'sesi':          sesi,
        'kolom_json':    json.dumps(kolom),
        'baris_mulai':   baris_mulai,
        'peserta_nama':  sesi.get_peserta_nama(),
        'detik_per_baris': sesi.detik_per_baris,
        'jumlah_baris':  sesi.jumlah_baris,
        'digit_per_baris': sesi.digit_per_baris,
    })


@csrf_exempt
@require_POST
def kraepelin_submit_baris(request, token):
    """AJAX: kandidat submit jawaban satu baris."""
    sesi = get_object_or_404(KraepelinSession, token=token)

    if not sesi.is_accessible:
        return JsonResponse({'error': 'Sesi tidak dapat diakses.'}, status=403)

    try:
        data    = json.loads(request.body)
        baris   = int(data.get('baris', 0))          # 1-based
        jawaban = data.get('jawaban', [])             # list int
    except (ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({'error': 'Data tidak valid.'}, status=400)

    if not (1 <= baris <= sesi.jumlah_baris):
        return JsonResponse({'error': 'Nomor baris tidak valid.'}, status=400)

    # Generate kunci untuk baris ini
    kolom = _generate_kolom(sesi.seed, sesi.jumlah_baris, sesi.digit_per_baris)
    kunci = _kunci_baris(kolom[baris - 1])

    # Hitung benar/salah dari yang dikerjakan
    dikerjakan = len(jawaban)
    benar      = sum(1 for i, j in enumerate(jawaban) if i < len(kunci) and j == kunci[i])
    salah      = dikerjakan - benar

    KraepelinRowResult.objects.update_or_create(
        session=sesi,
        baris=baris,
        defaults={
            'jawaban':    ','.join(str(j) for j in jawaban),
            'kunci':      ','.join(str(k) for k in kunci[:dikerjakan]),
            'dikerjakan': dikerjakan,
            'benar':      benar,
            'salah':      salah,
        }
    )

    # Cek apakah semua baris sudah selesai
    total_selesai = sesi.row_results.count()
    semua_selesai = total_selesai >= sesi.jumlah_baris

    return JsonResponse({
        'ok':            True,
        'baris':         baris,
        'dikerjakan':    dikerjakan,
        'benar':         benar,
        'semua_selesai': semua_selesai,
    })


def kraepelin_selesai(request, token):
    """Halaman setelah tes selesai — trigger scoring jika belum."""
    sesi = get_object_or_404(KraepelinSession, token=token)

    # Auto-hitung hasil jika belum ada
    result = getattr(sesi, 'result', None)
    if not result and sesi.row_results.exists():
        result = _hitung_kraepelin(sesi)

    return render(request, 'psychotest/kraepelin_selesai.html', {
        'sesi':   sesi,
        'result': result,
    })


# ─────────────────────────────────────────────────────────────────────────────
# HR — LIHAT HASIL DETAIL
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@addon_required('psychotest')
def kraepelin_result_hr(request, pk):
    """HR lihat hasil Kraepelin detail."""
    sesi   = get_object_or_404(KraepelinSession, pk=pk)
    result = getattr(sesi, 'result', None)

    if not result and sesi.row_results.exists():
        result = _hitung_kraepelin(sesi)

    rows = sesi.row_results.order_by('baris')
    return render(request, 'psychotest/kraepelin_result.html', {
        'sesi':   sesi,
        'result': result,
        'rows':   rows,
    })


@login_required
@addon_required('psychotest')
def kraepelin_session_list(request):
    """HR lihat semua sesi Kraepelin."""
    sessions = KraepelinSession.objects.select_related(
        'candidate', 'employee'
    ).order_by('-created_at')
    return render(request, 'psychotest/kraepelin_list.html', {'sessions': sessions})
