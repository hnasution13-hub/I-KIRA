"""
apps/recruitment/views_portal.py

Views untuk Portal Kandidat:
  - candidate_profile_send     : HR kirim/regenerate token via email
  - candidate_portal_form      : PUBLIC — kandidat isi data via token
  - candidate_profile_detail   : HR review data yang sudah diisi
  - candidate_promote          : HR promote CandidateProfile → Employee
  - portal_anak_save           : AJAX simpan/update data anak
  - portal_anak_delete         : AJAX hapus data anak
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Candidate
from .models_profile import CandidateProfile, CandidateAnak
from apps.core.decorators import hr_required

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  HR — KIRIM / REGENERATE TOKEN
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@hr_required
def candidate_profile_send(request, pk):
    """HR generate token dan kirim link ke email kandidat."""
    candidate = get_object_or_404(Candidate, pk=pk)

    if not candidate.email:
        messages.error(request, 'Kandidat tidak memiliki email — tidak bisa kirim link form.')
        return redirect('candidate_detail', pk=pk)

    # Get or create profile
    profile, created = CandidateProfile.objects.get_or_create(candidate=candidate)

    # Regenerate token (selalu — agar link selalu fresh)
    profile.regenerate_token()

    # Kirim email
    _send_portal_email(candidate, profile, request)

    if created:
        messages.success(request, f'Link form data diri berhasil dikirim ke {candidate.email}.')
    else:
        messages.success(request, f'Link form data diri berhasil dikirim ulang ke {candidate.email}.')

    return redirect('candidate_detail', pk=pk)


def _send_portal_email(candidate, profile, request):
    """Helper: kirim email link portal ke kandidat."""
    from django.conf import settings
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string

    site_url = getattr(settings, 'SITE_URL', request.build_absolute_uri('/').rstrip('/'))
    form_url = f"{site_url}/recruitment/portal/{profile.token}/"

    subject = f'[{getattr(settings, "APP_NAME", "HRIS")}] Mohon Lengkapi Data Diri Anda'
    context = {
        'candidate': candidate,
        'form_url': form_url,
        'token_expires_at': profile.token_expires_at,
        'app_name': getattr(settings, 'APP_NAME', 'HRIS SmartDesk'),
    }

    try:
        html_content = render_to_string('recruitment/email_portal_kandidat.html', context)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=(
                f"Yth. {candidate.nama},\n\n"
                f"Mohon lengkapi data diri Anda melalui link berikut:\n{form_url}\n\n"
                f"Link berlaku hingga {profile.token_expires_at.strftime('%d %B %Y %H:%M')} WIB.\n\n"
                f"Terima kasih."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[candidate.email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        logger.info(f'Portal email sent to {candidate.email} (candidate_id={candidate.pk})')
    except Exception as e:
        logger.error(f'Gagal kirim portal email ke {candidate.email}: {e}')


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC — FORM PENGISIAN KANDIDAT (NO LOGIN)
# ══════════════════════════════════════════════════════════════════════════════

def candidate_portal_form(request, token):
    """
    View publik — kandidat buka link ini tanpa login.
    Bisa diakses berkali-kali selama belum Hired dan token masih valid.
    """
    profile = get_object_or_404(CandidateProfile, token=token)
    candidate = profile.candidate

    # Cek token expired
    if not profile.is_token_valid:
        return render(request, 'recruitment/portal_expired.html', {
            'candidate': candidate,
        })

    # Cek sudah Hired — form dikunci
    is_locked = candidate.status == 'Hired'

    if request.method == 'POST' and not is_locked:
        _save_profile_from_post(profile, request.POST, request.FILES)

        # Mark submitted
        if not profile.is_submitted:
            profile.is_submitted = True
            profile.submitted_at = timezone.now()
            profile.save(update_fields=['is_submitted', 'submitted_at'])
        else:
            profile.save()

        # Notifikasi HR via email
        _notify_hr_submitted(candidate, profile, request)

        messages.success(request, 'Data diri berhasil disimpan. Terima kasih!')
        return redirect('candidate_portal_form', token=token)

    # Load data wilayah untuk dropdown
    from apps.wilayah.models import Provinsi, Kabupaten
    provinsi_list = Provinsi.objects.all().order_by('nama')
    kabupaten_list = (
        Kabupaten.objects.filter(provinsi=profile.provinsi).order_by('nama')
        if profile.provinsi else Kabupaten.objects.none()
    )
    anak_list = profile.anak_list.all()

    return render(request, 'recruitment/portal_form.html', {
        'profile':         profile,
        'candidate':       candidate,
        'is_locked':       is_locked,
        'provinsi_list':   provinsi_list,
        'kabupaten_list':  kabupaten_list,
        'anak_list':       anak_list,
    })


def _save_profile_from_post(profile, POST, FILES):
    """Helper: update CandidateProfile dari POST data."""
    CHAR_FIELDS = [
        'tempat_lahir', 'jenis_kelamin', 'agama', 'pendidikan',
        'golongan_darah', 'status_nikah', 'ptkp',
        'no_ktp', 'no_kk', 'no_npwp', 'no_bpjs_kes', 'no_bpjs_tk',
        'no_rek', 'nama_bank', 'nama_rek',
        'alamat', 'rt', 'rw', 'kode_pos', 'kecamatan', 'kelurahan',
        'nama_darurat', 'hub_darurat', 'hp_darurat',
    ]
    for field in CHAR_FIELDS:
        val = POST.get(field, '').strip()
        setattr(profile, field, val)

    # Int fields
    try:
        profile.jumlah_anak = int(POST.get('jumlah_anak', 0) or 0)
    except (ValueError, TypeError):
        profile.jumlah_anak = 0

    # Date fields
    tgl = POST.get('tanggal_lahir', '').strip()
    profile.tanggal_lahir = tgl if tgl else None

    # FK fields
    provinsi_id = POST.get('provinsi') or None
    kabupaten_id = POST.get('kabupaten') or None
    profile.provinsi_id = provinsi_id
    profile.kabupaten_id = kabupaten_id

    # File uploads
    for file_field in ['foto', 'scan_ktp', 'scan_ijazah', 'scan_skck', 'scan_npwp']:
        if file_field in FILES:
            setattr(profile, file_field, FILES[file_field])

    profile.save()


def _notify_hr_submitted(candidate, profile, request):
    """Kirim notifikasi email ke HR saat kandidat submit form."""
    from django.conf import settings
    from django.core.mail import send_mail

    hr_emails = getattr(settings, 'HR_EMAIL_LIST', [])
    if not hr_emails:
        return

    site_url = getattr(settings, 'SITE_URL', request.build_absolute_uri('/').rstrip('/'))
    detail_url = f"{site_url}/recruitment/candidates/{candidate.pk}/"

    subject = f'[HRIS] {candidate.nama} telah mengisi form data diri'
    body = (
        f"Kandidat {candidate.nama} ({candidate.jabatan_dilamar}) "
        f"telah melengkapi form data diri.\n\n"
        f"Kelengkapan data: {profile.completion_pct}%\n\n"
        f"Review di: {detail_url}\n\n"
        f"— HRIS SmartDesk"
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, hr_emails)
    except Exception as e:
        logger.error(f'Gagal kirim notif HR: {e}')


# ══════════════════════════════════════════════════════════════════════════════
#  AJAX — DATA ANAK
# ══════════════════════════════════════════════════════════════════════════════

@require_POST
def portal_anak_save(request, token):
    """AJAX: simpan/update data anak dari form publik."""
    profile = get_object_or_404(CandidateProfile, token=token)

    if not profile.is_token_valid or profile.candidate.status == 'Hired':
        return JsonResponse({'error': 'Akses ditolak'}, status=403)

    urutan   = int(request.POST.get('urutan', 0) or 0)
    nama     = request.POST.get('nama', '').strip()
    tgl      = request.POST.get('tgl_lahir', '').strip() or None
    jk       = request.POST.get('jenis_kelamin', '').strip()
    bpjs     = request.POST.get('no_bpjs_kes', '').strip()

    if not nama or not urutan:
        return JsonResponse({'error': 'Nama dan urutan wajib diisi'}, status=400)

    anak, _ = CandidateAnak.objects.update_or_create(
        profile=profile,
        urutan=urutan,
        defaults={
            'nama':          nama,
            'tgl_lahir':     tgl,
            'jenis_kelamin': jk,
            'no_bpjs_kes':   bpjs,
        }
    )
    return JsonResponse({'ok': True, 'id': anak.pk, 'nama': anak.nama})


@require_POST
def portal_anak_delete(request, token, anak_pk):
    """AJAX: hapus data anak."""
    profile = get_object_or_404(CandidateProfile, token=token)

    if not profile.is_token_valid or profile.candidate.status == 'Hired':
        return JsonResponse({'error': 'Akses ditolak'}, status=403)

    CandidateAnak.objects.filter(pk=anak_pk, profile=profile).delete()
    return JsonResponse({'ok': True})


# ══════════════════════════════════════════════════════════════════════════════
#  HR — REVIEW PROFIL
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def candidate_profile_detail(request, pk):
    """HR review data profil yang sudah diisi kandidat."""
    candidate = get_object_or_404(Candidate, pk=pk)
    profile   = get_object_or_404(CandidateProfile, candidate=candidate)

    if request.method == 'POST' and request.POST.get('action') == 'mark_reviewed':
        profile.is_reviewed = True
        profile.reviewed_by = request.user.get_full_name() or request.user.username
        profile.reviewed_at = timezone.now()
        profile.save(update_fields=['is_reviewed', 'reviewed_by', 'reviewed_at'])
        messages.success(request, 'Profil kandidat ditandai sudah di-review.')
        return redirect('candidate_profile_detail', pk=pk)

    return render(request, 'recruitment/portal_detail_hr.html', {
        'candidate': candidate,
        'profile':   profile,
        'anak_list': profile.anak_list.all(),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  HR — PROMOTE TO EMPLOYEE
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@hr_required
@require_POST
def candidate_promote(request, pk):
    """
    Promote CandidateProfile → Employee.
    Dipanggil saat kandidat di-Hired.
    Data dari CandidateProfile di-copy ke Employee baru.
    """
    candidate = get_object_or_404(Candidate, pk=pk)

    if candidate.status != 'Hired':
        messages.error(request, 'Kandidat belum berstatus Hired.')
        return redirect('candidate_detail', pk=pk)

    profile = getattr(candidate, 'profile', None)
    if not profile or not profile.is_submitted:
        messages.error(request, 'Kandidat belum mengisi form data diri.')
        return redirect('candidate_detail', pk=pk)

    # Cek sudah pernah di-promote
    from apps.employees.models import Employee
    company = getattr(request, 'company', None)
    if not company and getattr(request.user, 'is_superuser', False):
        from apps.core.models import Company
        company = Company.objects.first()

    if not company:
        messages.error(request, 'Company tidak ditemukan.')
        return redirect('candidate_detail', pk=pk)

    # Ambil data jabatan & join_date dari offering letter (kalau ada)
    offering = candidate.offering_letters.filter(
        status='Accepted'
    ).order_by('-tanggal_surat').first()
    if not offering:
        offering = candidate.offering_letters.order_by('-tanggal_surat').first()

    # Generate NIK sementara (HR bisa ubah setelah)
    import uuid as _uuid
    nik_temp = f'TMP-{_uuid.uuid4().hex[:8].upper()}'

    # Pastikan NIK unik di company ini
    while Employee.objects.filter(company=company, nik=nik_temp).exists():
        nik_temp = f'TMP-{_uuid.uuid4().hex[:8].upper()}'

    emp_data = {
        'company':        company,
        'nik':            nik_temp,
        'nama':           candidate.nama,
        'email':          candidate.email,
        'no_hp':          candidate.no_hp,
        'status':         'Aktif',
        'status_karyawan': offering.status_karyawan if offering else 'PKWT',
        'join_date':      offering.tanggal_mulai_kerja if offering else timezone.now().date(),
        # Data dari profile
        'tempat_lahir':   profile.tempat_lahir,
        'tanggal_lahir':  profile.tanggal_lahir,
        'jenis_kelamin':  profile.jenis_kelamin,
        'agama':          profile.agama,
        'pendidikan':     profile.pendidikan,
        'golongan_darah': profile.golongan_darah,
        'status_nikah':   profile.status_nikah,
        'jumlah_anak':    profile.jumlah_anak,
        'ptkp':           profile.ptkp,
        'no_ktp':         profile.no_ktp,
        'no_kk':          profile.no_kk,
        'no_npwp':        profile.no_npwp,
        'no_bpjs_kes':    profile.no_bpjs_kes,
        'no_bpjs_tk':     profile.no_bpjs_tk,
        'no_rek':         profile.no_rek,
        'nama_bank':      profile.nama_bank,
        'nama_rek':       profile.nama_rek,
        'alamat':         profile.alamat,
        'rt':             profile.rt,
        'rw':             profile.rw,
        'kode_pos':       profile.kode_pos,
        'provinsi':       profile.provinsi,
        'kabupaten':      profile.kabupaten,
        'kecamatan':      profile.kecamatan,
        'kelurahan':      profile.kelurahan,
        'nama_darurat':   profile.nama_darurat,
        'hub_darurat':    profile.hub_darurat,
        'hp_darurat':     profile.hp_darurat,
        'gaji_pokok':     offering.gaji_pokok if offering else 0,
    }

    # Jabatan & department dari offering
    if offering:
        from apps.core.models import Department, Position
        dept = offering.department
        pos  = Position.objects.filter(nama__iexact=offering.jabatan).first()
        if dept:
            emp_data['department'] = dept
        if pos:
            emp_data['jabatan'] = pos

    try:
        employee = Employee.objects.create(**emp_data)

        # Copy foto dari profile ke employee
        if profile.foto:
            from django.core.files.base import ContentFile
            try:
                employee.foto.save(
                    f'emp_{employee.pk}.jpg',
                    ContentFile(profile.foto.read()),
                    save=True,
                )
            except Exception as e:
                logger.warning(f'Gagal copy foto ke employee: {e}')

        # Copy data anak
        from apps.employees.models import AnakKaryawan
        for anak in profile.anak_list.all():
            AnakKaryawan.objects.create(
                employee=employee,
                urutan=anak.urutan,
                nama=anak.nama,
                tgl_lahir=anak.tgl_lahir,
                jenis_kelamin=anak.jenis_kelamin,
                no_bpjs_kes=anak.no_bpjs_kes,
            )

        messages.success(
            request,
            f'✅ Kandidat {candidate.nama} berhasil dipromote menjadi karyawan. '
            f'NIK sementara: {nik_temp} — mohon diperbarui di data karyawan.'
        )
        return redirect('employee_detail', pk=employee.pk)

    except Exception as e:
        logger.error(f'Gagal promote kandidat {candidate.pk} ke employee: {e}')
        messages.error(request, f'Gagal promote: {e}')
        return redirect('candidate_detail', pk=pk)
