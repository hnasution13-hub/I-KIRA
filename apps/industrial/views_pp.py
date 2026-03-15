"""
Tambahkan ke apps/industrial/views_surat.py
(atau buat file baru: apps/industrial/views_pp.py)

View untuk upload & kelola dokumen Peraturan Perusahaan SP.
"""
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_POST

from apps.core.utils import get_company_qs
from .models import PeraturanPerusahaanSP


# ── Allowed extensions ────────────────────────────────────────────────────────
ALLOWED_EXT  = {'.pdf', '.docx', '.doc', '.xlsx', '.xls'}
MAX_SIZE_MB  = 10


def _detect_jenis(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.pdf':
        return 'pdf'
    if ext in ('.docx', '.doc'):
        return 'docx'
    return 'other'


# ══════════════════════════════════════════════════════════════════════════════
#  LIST + UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def pp_sp_list(request):
    """Daftar dokumen PP SP & form upload."""
    company = getattr(request, 'company', None)
    docs    = PeraturanPerusahaanSP.objects.filter(company=company).order_by('-created_at') if company else PeraturanPerusahaanSP.objects.none()

    if request.method == 'POST':
        file    = request.FILES.get('dokumen')
        judul   = request.POST.get('judul', '').strip()
        versi   = request.POST.get('versi', '').strip()
        keterangan = request.POST.get('keterangan', '').strip()
        set_aktif  = request.POST.get('is_aktif') == 'on'

        # Validasi
        if not file:
            messages.error(request, 'File dokumen wajib diunggah.')
            return redirect('pp_sp_list')

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_EXT:
            messages.error(request, f'Ekstensi file tidak didukung ({ext}). Gunakan: {", ".join(ALLOWED_EXT)}')
            return redirect('pp_sp_list')

        if file.size > MAX_SIZE_MB * 1024 * 1024:
            messages.error(request, f'Ukuran file melebihi batas {MAX_SIZE_MB} MB.')
            return redirect('pp_sp_list')

        if not judul:
            judul = file.name

        # Jika set aktif → nonaktifkan yg lain
        if set_aktif:
            PeraturanPerusahaanSP.objects.filter(company=company).update(is_aktif=False)

        user_label = request.user.get_full_name() or request.user.username

        doc = PeraturanPerusahaanSP.objects.create(
            company       = company,
            judul         = judul,
            versi         = versi,
            dokumen       = file,
            jenis         = _detect_jenis(file.name),
            keterangan    = keterangan,
            is_aktif      = set_aktif,
            diunggah_oleh = user_label,
        )

        messages.success(request, f'Dokumen "<strong>{doc.judul}</strong>" berhasil diunggah.')
        return redirect('pp_sp_list')

    aktif_doc = docs.filter(is_aktif=True).first()
    return render(request, 'industrial/pp_sp_list.html', {
        'docs'      : docs,
        'aktif_doc' : aktif_doc,
        'company'   : company,
    })


# ── Toggle aktif ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def pp_sp_toggle_aktif(request, pk):
    company = getattr(request, 'company', None)
    doc = get_object_or_404(PeraturanPerusahaanSP, pk=pk, company=company)

    # Nonaktifkan semua lalu aktifkan yang dipilih
    PeraturanPerusahaanSP.objects.filter(company=company).update(is_aktif=False)
    doc.is_aktif = True
    doc.save(update_fields=['is_aktif'])
    messages.success(request, f'Dokumen "<strong>{doc.judul}</strong>" sekarang menjadi dokumen aktif.')
    return redirect('pp_sp_list')


# ── Delete ────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def pp_sp_delete(request, pk):
    company = getattr(request, 'company', None)
    doc = get_object_or_404(PeraturanPerusahaanSP, pk=pk, company=company)
    nama = doc.judul
    # Hapus file fisik
    try:
        if doc.dokumen:
            doc.dokumen.delete(save=False)
    except Exception:
        pass
    doc.delete()
    messages.warning(request, f'Dokumen "<strong>{nama}</strong>" telah dihapus.')
    return redirect('pp_sp_list')


# ── Download / Preview ────────────────────────────────────────────────────────

@login_required
def pp_sp_download(request, pk):
    company = getattr(request, 'company', None)
    doc = get_object_or_404(PeraturanPerusahaanSP, pk=pk, company=company)
    try:
        return FileResponse(doc.dokumen.open('rb'), as_attachment=True, filename=doc.filename)
    except Exception:
        raise Http404('File tidak ditemukan.')
