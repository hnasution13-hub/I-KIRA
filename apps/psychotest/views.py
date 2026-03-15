"""
apps/psychotest/views.py
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from apps.core.addon_decorators import addon_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    SoalBank, PsikotesSession, PsikotesAnswer, PsikotesResult,
    MedicalCheckUp, InterviewSession, Rekomendasi, OnboardingChecklist,
)
from apps.recruitment.models import Candidate
from utils.psychotest_seed import DISC_DESKRIPSI


# ─────────────────────────────────────────────────────────────────────────────
# HR — SOAL BANK MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@addon_required('psychotest')
def soal_bank_list(request):
    kategori = request.GET.get('kategori', '')
    qs = SoalBank.objects.all()
    if kategori:
        qs = qs.filter(kategori=kategori)
    return render(request, 'psychotest/soal_bank_list.html', {
        'soal_list': qs,
        'kategori': kategori,
        'kategori_choices': SoalBank.KATEGORI_CHOICES,
    })


@login_required
@addon_required('psychotest')
def soal_bank_form(request, pk=None):
    instance = get_object_or_404(SoalBank, pk=pk) if pk else None
    if request.method == 'POST':
        data = {
            'kategori':      request.POST.get('kategori'),
            'tipe':          request.POST.get('tipe', 'pilihan_ganda'),
            'pertanyaan':    request.POST.get('pertanyaan'),
            'opsi_a':        request.POST.get('opsi_a', ''),
            'opsi_b':        request.POST.get('opsi_b', ''),
            'opsi_c':        request.POST.get('opsi_c', ''),
            'opsi_d':        request.POST.get('opsi_d', ''),
            'jawaban_benar': request.POST.get('jawaban_benar', ''),
            'disc_a':        request.POST.get('disc_a', ''),
            'disc_b':        request.POST.get('disc_b', ''),
            'disc_c':        request.POST.get('disc_c', ''),
            'disc_d':        request.POST.get('disc_d', ''),
            'urutan':        int(request.POST.get('urutan', 0) or 0),
            'aktif':         request.POST.get('aktif') == 'on',
        }
        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()
            messages.success(request, 'Soal berhasil diperbarui.')
        else:
            SoalBank.objects.create(**data)
            messages.success(request, 'Soal berhasil ditambahkan.')
        return redirect('soal_bank_list')
    return render(request, 'psychotest/soal_bank_form.html', {
        'instance': instance,
        'kategori_choices': SoalBank.KATEGORI_CHOICES,
        'tipe_choices': SoalBank.TIPE_CHOICES,
    })


@login_required
@require_POST
def soal_bank_delete(request, pk):
    soal = get_object_or_404(SoalBank, pk=pk)
    soal.delete()
    messages.success(request, 'Soal dihapus.')
    return redirect('soal_bank_list')


# ─────────────────────────────────────────────────────────────────────────────
# HR — SESI PSIKOTES
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@addon_required('psychotest')
def session_list(request):
    sessions = PsikotesSession.objects.select_related('candidate').order_by('-created_at')
    return render(request, 'psychotest/session_list.html', {'sessions': sessions})


@login_required
@addon_required('psychotest')
def session_create(request, candidate_pk):
    """HR buat sesi psikotes baru untuk kandidat."""
    candidate = get_object_or_404(Candidate, pk=candidate_pk)

    if request.method == 'POST':
        paket = request.POST.getlist('paket')  # ['logika','verbal','numerik','disc']
        if not paket:
            messages.error(request, 'Pilih minimal satu paket tes.')
            return redirect('session_create', candidate_pk=candidate_pk)

        from datetime import timedelta
        expired_days = int(request.POST.get('expired_days', 7))

        session = PsikotesSession.objects.create(
            candidate=candidate,
            paket=paket,
            expired_at=timezone.now() + timedelta(days=expired_days),
            durasi_logika=int(request.POST.get('durasi_logika', 15)),
            durasi_verbal=int(request.POST.get('durasi_verbal', 15)),
            durasi_numerik=int(request.POST.get('durasi_numerik', 15)),
            durasi_disc=int(request.POST.get('durasi_disc', 20)),
            created_by=request.user.get_full_name() or request.user.username,
        )

        link_full = request.build_absolute_uri(f'/psychotest/tes/{session.token}/')
        messages.success(request, f'Sesi psikotes berhasil dibuat. Link: {link_full}')
        return redirect('candidate_detail', pk=candidate_pk)

    return render(request, 'psychotest/session_create.html', {
        'candidate': candidate,
        'kategori_choices': SoalBank.KATEGORI_CHOICES,
    })


@login_required
@addon_required('psychotest')
def session_detail(request, pk):
    session = get_object_or_404(PsikotesSession, pk=pk)
    result = getattr(session, 'result', None)
    answers = session.answers.select_related('soal').all()
    link_full = request.build_absolute_uri(f'/psychotest/tes/{session.token}/')
    return render(request, 'psychotest/session_detail.html', {
        'session': session,
        'result': result,
        'answers': answers,
        'link_full': link_full,
        'disc_deskripsi': DISC_DESKRIPSI,
    })


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC — KANDIDAT KERJAKAN TES (tanpa login)
# ─────────────────────────────────────────────────────────────────────────────

def tes_intro(request, token):
    """Halaman intro sebelum tes dimulai."""
    session = get_object_or_404(PsikotesSession, token=token)

    if session.status == 'completed':
        return render(request, 'psychotest/tes_done.html', {'session': session})

    if session.is_expired:
        session.status = 'expired'
        session.save()
        return render(request, 'psychotest/tes_expired.html', {'session': session})

    return render(request, 'psychotest/tes_intro.html', {
        'session': session,
        'paket': session.paket,
    })


def tes_mulai(request, token):
    """Mulai tes — tampilkan soal per kategori."""
    session = get_object_or_404(PsikotesSession, token=token)

    if session.status == 'completed':
        return redirect('tes_selesai', token=token)
    if session.is_expired:
        return render(request, 'psychotest/tes_expired.html', {'session': session})

    # Update status ke started
    if session.status == 'pending':
        session.status = 'started'
        session.started_at = timezone.now()
        session.save()

    # Tentukan kategori aktif (dari query param atau pertama di paket)
    kategori_aktif = request.GET.get('kategori', session.paket[0] if session.paket else 'logika')

    # Ambil soal untuk kategori ini
    soal_list = list(
        SoalBank.objects.filter(kategori=kategori_aktif, aktif=True).order_by('urutan', 'id')
    )

    # Ambil jawaban yang sudah ada — preprocess jadi format template-friendly
    existing_answers = {
        a.soal_id: a for a in session.answers.filter(soal__kategori=kategori_aktif)
    }

    # Buat dict tambahan yang bisa dibaca template tanpa custom filter:
    # existing_jawaban[soal_id]      → jawaban pilihan ganda (A/B/C/D)
    # existing_disc_most[soal_id]    → jawaban DISC most
    # existing_disc_least[soal_id]   → jawaban DISC least
    existing_jawaban    = {sid: a.jawaban    for sid, a in existing_answers.items()}
    existing_disc_most  = {sid: a.disc_most  for sid, a in existing_answers.items()}
    existing_disc_least = {sid: a.disc_least for sid, a in existing_answers.items()}

    if request.method == 'POST':
        # Simpan jawaban kategori ini
        for soal in soal_list:
            if soal.tipe == 'disc_set':
                most  = request.POST.get(f'most_{soal.id}', '')
                least = request.POST.get(f'least_{soal.id}', '')
                PsikotesAnswer.objects.update_or_create(
                    session=session, soal=soal,
                    defaults={'disc_most': most, 'disc_least': least}
                )
            else:
                jawaban = request.POST.get(f'soal_{soal.id}', '')
                PsikotesAnswer.objects.update_or_create(
                    session=session, soal=soal,
                    defaults={'jawaban': jawaban}
                )

        # Pindah ke kategori berikutnya atau selesai
        paket = session.paket
        idx = paket.index(kategori_aktif) if kategori_aktif in paket else 0
        if idx + 1 < len(paket):
            next_kat = paket[idx + 1]
            return redirect(f'/psychotest/tes/{token}/mulai/?kategori={next_kat}')
        else:
            # Semua kategori selesai → hitung skor
            _hitung_dan_simpan_hasil(session)
            return redirect('tes_selesai', token=token)

    # Nomor urut soal global (untuk tampilan "Soal X dari Y")
    soal_nomor_start = 1
    for kat in session.paket:
        if kat == kategori_aktif:
            break
        soal_nomor_start += SoalBank.objects.filter(kategori=kat, aktif=True).count()

    durasi = getattr(session, f'durasi_{kategori_aktif}', 15)

    return render(request, 'psychotest/tes_soal.html', {
        'session':            session,
        'kategori_aktif':     kategori_aktif,
        'kategori_label':     dict(SoalBank.KATEGORI_CHOICES).get(kategori_aktif, kategori_aktif),
        'soal_list':          soal_list,
        'existing_answers':   existing_answers,
        'existing_jawaban':   existing_jawaban,
        'existing_disc_most': existing_disc_most,
        'existing_disc_least':existing_disc_least,
        'paket':              session.paket,
        'kategori_aktif_idx': session.paket.index(kategori_aktif) if kategori_aktif in session.paket else 0,
        'soal_nomor_start':   soal_nomor_start,
        'durasi_menit':       durasi,
        'token':              token,
    })


def tes_selesai(request, token):
    """Halaman hasil setelah tes selesai."""
    session = get_object_or_404(PsikotesSession, token=token)
    result  = getattr(session, 'result', None)
    return render(request, 'psychotest/tes_selesai.html', {
        'session': session,
        'result':  result,
        'disc_deskripsi': DISC_DESKRIPSI,
    })


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _hitung_dan_simpan_hasil(session: PsikotesSession):
    """Hitung semua skor dan simpan ke PsikotesResult + update Candidate."""
    answers = list(session.answers.select_related('soal').all())
    paket   = session.paket
    detail  = {}

    skor_per_kat = {}

    # ── Hitung skor pilihan ganda (logika/verbal/numerik) ──────────────────
    for kat in ['logika', 'verbal', 'numerik']:
        if kat not in paket:
            continue
        soal_kat = [a for a in answers if a.soal.kategori == kat]
        if not soal_kat:
            continue
        benar = sum(1 for a in soal_kat if a.is_correct)
        total = len(soal_kat)
        skor  = round(benar / total * 100) if total > 0 else 0
        skor_per_kat[kat] = skor
        detail[kat] = {'benar': benar, 'total': total, 'skor': skor}

    # ── Hitung DISC ────────────────────────────────────────────────────────
    disc_scores = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
    if 'disc' in paket:
        disc_answers = [a for a in answers if a.soal.kategori == 'disc']
        for a in disc_answers:
            # MOST +2 poin untuk dimensi itu
            if a.disc_most:
                dim_most = getattr(a.soal, f'disc_{a.disc_most.lower()}', '')
                if dim_most in disc_scores:
                    disc_scores[dim_most] += 2
            # LEAST -1 poin
            if a.disc_least:
                dim_least = getattr(a.soal, f'disc_{a.disc_least.lower()}', '')
                if dim_least in disc_scores:
                    disc_scores[dim_least] = max(0, disc_scores[dim_least] - 1)

        # Normalisasi ke 0-100
        max_disc = max(disc_scores.values()) if any(disc_scores.values()) else 1
        disc_norm = {k: round(v / max_disc * 100) for k, v in disc_scores.items()} if max_disc > 0 else disc_scores
        detail['disc'] = disc_norm

        # Profil dominan (1 atau 2 tertinggi)
        sorted_disc = sorted(disc_norm.items(), key=lambda x: x[1], reverse=True)
        profil = sorted_disc[0][0]
        if len(sorted_disc) > 1 and sorted_disc[1][1] >= sorted_disc[0][1] * 0.8:
            profil = sorted_disc[0][0] + sorted_disc[1][0]

        disc_deskripsi = DISC_DESKRIPSI.get(sorted_disc[0][0], {})
    else:
        disc_norm = disc_scores
        profil = ''
        disc_deskripsi = {}

    # ── Skor total psikotes (rata-rata kognitif saja) ─────────────────────
    kognitif_scores = [v for k, v in skor_per_kat.items()]
    skor_total = round(sum(kognitif_scores) / len(kognitif_scores)) if kognitif_scores else 50

    grade = 'A' if skor_total >= 80 else 'B' if skor_total >= 65 else 'C' if skor_total >= 50 else 'D'

    # ── Simpan hasil ───────────────────────────────────────────────────────
    result, _ = PsikotesResult.objects.update_or_create(
        session=session,
        defaults={
            'candidate':      session.candidate,
            'skor_logika':    skor_per_kat.get('logika'),
            'skor_verbal':    skor_per_kat.get('verbal'),
            'skor_numerik':   skor_per_kat.get('numerik'),
            'skor_total':     skor_total,
            'disc_d':         disc_norm.get('D', 0),
            'disc_i':         disc_norm.get('I', 0),
            'disc_s':         disc_norm.get('S', 0),
            'disc_c':         disc_norm.get('C', 0),
            'disc_profil':    profil,
            'disc_deskripsi': disc_deskripsi.get('deskripsi', ''),
            'grade':          grade,
            'detail':         detail,
        }
    )

    # Update session status
    session.status = 'completed'
    session.completed_at = timezone.now()
    session.save()

    # Update Candidate — psikotes_score + total_score
    candidate = session.candidate
    candidate.psikotes_score    = skor_total
    candidate.psikotes_grade    = grade
    candidate.psikotes_detail   = {
        'skor_logika':  skor_per_kat.get('logika'),
        'skor_verbal':  skor_per_kat.get('verbal'),
        'skor_numerik': skor_per_kat.get('numerik'),
        'skor_total':   skor_total,
        'disc_profil':  profil,
        'disc_scores':  disc_norm,
        'detail':       detail,
    }
    candidate.save()

    return result


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE — MEDICAL CHECK UP
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@addon_required('psychotest')
def mcu_form(request, candidate_pk):
    candidate = get_object_or_404(Candidate, pk=candidate_pk)
    instance, _ = MedicalCheckUp.objects.get_or_create(candidate=candidate)

    if request.method == 'POST':
        instance.status      = request.POST.get('status', 'pending')
        instance.tanggal_mcu = request.POST.get('tanggal_mcu') or None
        instance.faskes      = request.POST.get('faskes', '')
        instance.catatan     = request.POST.get('catatan', '')
        if 'file_hasil' in request.FILES:
            instance.file_hasil = request.FILES['file_hasil']
        if request.user.is_authenticated:
            instance.approved_by = request.user.get_full_name() or request.user.username
            instance.approved_at = timezone.now()
        instance.save()

        # Kalau Unfit → otomatis Rejected
        if instance.status == 'unfit':
            candidate.status = 'Rejected'
            candidate.save()
            messages.warning(request, f'{candidate.nama} dinyatakan Unfit MCU dan otomatis ditolak.')
        else:
            messages.success(request, 'Data MCU berhasil disimpan.')

        return redirect('candidate_detail', pk=candidate_pk)

    return render(request, 'psychotest/mcu_form.html', {
        'candidate': candidate,
        'instance':  instance,
        'status_choices': MedicalCheckUp.STATUS_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE — INTERVIEW
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def interview_form(request, candidate_pk, pk=None):
    candidate = get_object_or_404(Candidate, pk=candidate_pk)
    instance  = get_object_or_404(InterviewSession, pk=pk) if pk else None

    if request.method == 'POST':
        data = {
            'candidate':           candidate,
            'tipe':                request.POST.get('tipe', 'hr'),
            'interviewer':         request.POST.get('interviewer', ''),
            'tanggal':             request.POST.get('tanggal'),
            'jam':                 request.POST.get('jam') or None,
            'lokasi':              request.POST.get('lokasi', ''),
            'nilai_technical':     _int_or_none(request.POST.get('nilai_technical')),
            'nilai_attitude':      _int_or_none(request.POST.get('nilai_attitude')),
            'nilai_communication': _int_or_none(request.POST.get('nilai_communication')),
            'nilai_culture_fit':   _int_or_none(request.POST.get('nilai_culture_fit')),
            'catatan':             request.POST.get('catatan', ''),
            'rekomendasi':         request.POST.get('rekomendasi', ''),
        }
        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()
        else:
            instance = InterviewSession.objects.create(**data)

        # Update interview_score di kandidat (rata-rata semua sesi yang sudah ada nilai)
        _update_interview_score(candidate)

        messages.success(request, 'Data interview berhasil disimpan.')
        return redirect('candidate_detail', pk=candidate_pk)

    return render(request, 'psychotest/interview_form.html', {
        'candidate': candidate,
        'instance':  instance,
        'tipe_choices': InterviewSession.TIPE_CHOICES,
    })


def _update_interview_score(candidate):
    sessions = InterviewSession.objects.filter(candidate=candidate)
    scores = [s.skor_rata for s in sessions if s.skor_rata is not None]
    if scores:
        candidate.interview_score = round(sum(scores) / len(scores))
        candidate.save()


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE — REKOMENDASI HR
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def rekomendasi_form(request, candidate_pk):
    candidate = get_object_or_404(Candidate, pk=candidate_pk)
    instance  = getattr(candidate, 'rekomendasi', None)

    if request.method == 'POST':
        keputusan = request.POST.get('keputusan')
        alasan    = request.POST.get('alasan', '')
        approver  = request.user.get_full_name() or request.user.username

        if instance:
            instance.keputusan   = keputusan
            instance.alasan      = alasan
            instance.approved_by = approver
            instance.approved_at = timezone.now()
            instance.save()
        else:
            instance = Rekomendasi.objects.create(
                candidate=candidate,
                keputusan=keputusan,
                alasan=alasan,
                approved_by=approver,
                approved_at=timezone.now(),
            )

        # Update status kandidat
        if keputusan == 'lanjut_offering':
            candidate.status = 'Offering'
            messages.success(request, f'{candidate.nama} dilanjutkan ke Offering Letter.')
        elif keputusan == 'tolak':
            candidate.status = 'Rejected'
            messages.warning(request, f'{candidate.nama} ditolak.')
        candidate.save()

        return redirect('candidate_detail', pk=candidate_pk)

    return render(request, 'psychotest/rekomendasi_form.html', {
        'candidate': candidate,
        'instance':  instance,
        'keputusan_choices': Rekomendasi.KEPUTUSAN_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE — ONBOARDING
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def onboarding_form(request, candidate_pk):
    candidate = get_object_or_404(Candidate, pk=candidate_pk)
    instance, _ = OnboardingChecklist.objects.get_or_create(candidate=candidate)

    if request.method == 'POST':
        instance.tanggal_mulai  = request.POST.get('tanggal_mulai') or None
        instance.masa_probasi   = int(request.POST.get('masa_probasi', 3) or 3)
        instance.catatan        = request.POST.get('catatan', '')

        # Dokumen checkboxes
        for field in ['doc_ktp','doc_ijazah','doc_skck','doc_foto',
                      'doc_npwp','doc_bpjs','doc_rekening','doc_kontrak']:
            setattr(instance, field, request.POST.get(field) == 'on')

        # Orientasi checkboxes
        for field in ['ori_perkenalan','ori_sop','ori_fasilitas','ori_sistem']:
            setattr(instance, field, request.POST.get(field) == 'on')

        instance.selesai = request.POST.get('selesai') == 'on'
        instance.save()

        # Auto-create employee jika checklist selesai dan diminta
        if request.POST.get('create_employee') == 'yes' and not instance.employee_created:
            success = _auto_create_employee(candidate, instance)
            if success:
                instance.employee_created = True
                instance.save()
                messages.success(request, f'Employee record untuk {candidate.nama} berhasil dibuat.')
            else:
                messages.warning(request, f'Employee record gagal dibuat secara otomatis. Silakan buat manual di modul Karyawan.')

        if instance.selesai:
            candidate.status = 'Hired'
            candidate.save()
            # Update MPRF jika ada
            if candidate.mprf:
                _check_mprf_filled(candidate.mprf)
            messages.success(request, f'Onboarding {candidate.nama} selesai — status: Hired!')
        else:
            messages.success(request, 'Checklist onboarding disimpan.')

        return redirect('candidate_detail', pk=candidate_pk)

    return render(request, 'psychotest/onboarding_form.html', {
        'candidate': candidate,
        'instance':  instance,
    })


def _auto_create_employee(candidate, onboarding):
    """Auto-create Employee record dari data kandidat. Return True jika berhasil."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        from apps.employees.models import Employee
        from datetime import date
        employee, created = Employee.objects.get_or_create(
            nama=candidate.nama,
            defaults={
                'email':             candidate.email,
                'no_hp':             candidate.no_hp,
                'tanggal_bergabung': onboarding.tanggal_mulai or date.today(),
                'status':            'Aktif',
            }
        )
        return True
    except Exception as e:
        logger.error(f'Auto-create employee gagal untuk kandidat pk={candidate.pk}: {e}')
        return False


def _check_mprf_filled(mprf):
    """Cek apakah kuota MPRF sudah terpenuhi."""
    hired_count = mprf.candidates.filter(status='Hired').count()
    if hired_count >= mprf.jumlah_kebutuhan:
        mprf.status = 'Filled'
        mprf.save()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _int_or_none(val):
    try:
        return int(val) if val not in (None, '', 'None') else None
    except (ValueError, TypeError):
        return None
