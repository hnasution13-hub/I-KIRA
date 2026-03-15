"""
apps/advanced_psychotest/emails.py

Utilitas pengiriman email notifikasi untuk Advanced Psychometric Test.
Dipanggil dari views saat sesi dibuat.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


def _get_base_url():
    """Return base URL dari settings, fallback ke localhost."""
    return getattr(settings, 'SITE_BASE_URL', 'http://localhost:8000')


def kirim_email_sesi_kandidat(session, request=None):
    """
    Kirim email notifikasi ke kandidat berisi link tes.
    Dipanggil setelah AdvSession untuk kandidat dibuat.
    """
    candidate = session.candidate
    if not candidate:
        return False

    email = getattr(candidate, 'email', None)
    if not email:
        return False

    from .models import TEST_TYPE_CHOICES
    tipe_labels = dict(TEST_TYPE_CHOICES)
    paket = session.get_paket()
    paket_label = ', '.join(tipe_labels.get(t, t) for t in paket)

    if request:
        link = request.build_absolute_uri(f'/advanced-test/tes/{session.token}/')
    else:
        link = f"{_get_base_url()}/advanced-test/tes/{session.token}/"

    expired_str = session.expired_at.strftime('%d %B %Y pukul %H:%M')

    subject = f'[HRIS SmartDesk] Undangan Tes Psikometri — {paket_label}'

    message = f"""Yth. {candidate.nama},

Anda diundang untuk mengikuti Tes Psikometri sebagai bagian dari proses seleksi.

Detail Tes:
  Paket  : {paket_label}
  Link   : {link}
  Berlaku: sampai {expired_str}

Petunjuk:
  1. Klik link di atas untuk membuka halaman tes.
  2. Pastikan koneksi internet stabil.
  3. Kerjakan sendiri tanpa bantuan alat bantu.
  4. Timer berjalan begitu Anda menekan tombol Mulai.
  5. Hasil tidak dapat diubah setelah disubmit.

Apabila ada pertanyaan, silakan hubungi tim HR kami.

Salam,
Tim HR — HRIS SmartDesk
"""

    html_message = f"""
<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#f4f6fb;margin:0;padding:20px;">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;
            box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden;">

  <!-- Header -->
  <div style="background:#7b1fa2;padding:28px 32px;">
    <h2 style="margin:0;color:#fff;font-size:1.3rem;">📋 Undangan Tes Psikometri</h2>
    <p style="margin:6px 0 0;color:#e1bee7;font-size:.9rem;">HRIS SmartDesk</p>
  </div>

  <!-- Body -->
  <div style="padding:28px 32px;">
    <p style="color:#424242;font-size:.95rem;">Yth. <strong>{candidate.nama}</strong>,</p>
    <p style="color:#424242;font-size:.92rem;line-height:1.6;">
      Anda diundang untuk mengikuti <strong>Tes Psikometri</strong> sebagai
      bagian dari proses seleksi.
    </p>

    <!-- Info box -->
    <div style="background:#f3e5f5;border-left:4px solid #7b1fa2;
                border-radius:6px;padding:16px 20px;margin:20px 0;">
      <table style="width:100%;border-collapse:collapse;font-size:.88rem;color:#424242;">
        <tr>
          <td style="padding:4px 0;width:90px;color:#888;">Paket Tes</td>
          <td style="padding:4px 0;font-weight:600;">{paket_label}</td>
        </tr>
        <tr>
          <td style="padding:4px 0;color:#888;">Berlaku s/d</td>
          <td style="padding:4px 0;font-weight:600;">{expired_str}</td>
        </tr>
      </table>
    </div>

    <!-- CTA Button -->
    <div style="text-align:center;margin:28px 0;">
      <a href="{link}"
         style="background:#7b1fa2;color:#fff;text-decoration:none;
                padding:14px 36px;border-radius:8px;font-weight:700;
                font-size:1rem;display:inline-block;">
        ▶ Mulai Tes Sekarang
      </a>
    </div>

    <p style="color:#888;font-size:.82rem;line-height:1.7;">
      Atau salin link berikut ke browser Anda:<br>
      <a href="{link}" style="color:#7b1fa2;word-break:break-all;">{link}</a>
    </p>

    <!-- Petunjuk -->
    <div style="background:#f8f8f8;border-radius:8px;padding:16px 20px;margin-top:20px;">
      <p style="margin:0 0 8px;font-weight:600;font-size:.88rem;color:#424242;">
        📌 Petunjuk Pengerjaan
      </p>
      <ul style="margin:0;padding-left:18px;font-size:.85rem;color:#666;line-height:1.9;">
        <li>Pastikan koneksi internet stabil selama tes berlangsung.</li>
        <li>Kerjakan sendiri tanpa bantuan orang lain atau alat bantu.</li>
        <li>Timer per tes berjalan begitu Anda menekan tombol Mulai.</li>
        <li>Tes otomatis disubmit saat waktu habis.</li>
        <li>Hasil tidak dapat diubah setelah disubmit.</li>
      </ul>
    </div>
  </div>

  <!-- Footer -->
  <div style="background:#f5f5f5;padding:16px 32px;text-align:center;
              font-size:.8rem;color:#aaa;">
    Email ini dikirim otomatis oleh HRIS SmartDesk.<br>
    Jangan balas email ini. Hubungi HR jika ada pertanyaan.
  </div>
</div>
</body>
</html>
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log error tapi jangan crash — sesi tetap dibuat
        import logging
        logging.getLogger(__name__).error(
            f'Gagal kirim email sesi tes ke {email}: {e}'
        )
        return False


def kirim_email_sesi_karyawan(session, request=None):
    """
    Kirim email notifikasi ke karyawan berisi link tes berkala.
    """
    employee = session.employee
    if not employee:
        return False

    email = getattr(employee, 'email', None)
    if not email:
        return False

    from .models import TEST_TYPE_CHOICES
    tipe_labels = dict(TEST_TYPE_CHOICES)
    paket = session.get_paket()
    paket_label = ', '.join(tipe_labels.get(t, t) for t in paket)

    if request:
        link = request.build_absolute_uri(f'/advanced-test/tes/{session.token}/')
    else:
        link = f"{_get_base_url()}/advanced-test/tes/{session.token}/"

    expired_str = session.expired_at.strftime('%d %B %Y pukul %H:%M')

    TUJUAN_LABEL = {
        'berkala':  'Evaluasi Berkala',
        'promosi':  'Pertimbangan Promosi',
        'evaluasi': 'Evaluasi Kinerja',
        'lainnya':  'Lainnya',
    }
    tujuan_label = TUJUAN_LABEL.get(session.tujuan, session.tujuan)

    subject = f'[HRIS SmartDesk] Jadwal Psikotes — {tujuan_label}'

    message = f"""Yth. {employee.nama},

Anda dijadwalkan untuk mengikuti Psikotes: {tujuan_label}.

Detail:
  Paket  : {paket_label}
  Tujuan : {tujuan_label}
  Link   : {link}
  Berlaku: sampai {expired_str}

Kerjakan sebelum batas waktu di atas.

Salam,
Tim HR — HRIS SmartDesk
"""

    html_message = f"""
<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#f4f6fb;margin:0;padding:20px;">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;
            box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden;">
  <div style="background:#1565c0;padding:28px 32px;">
    <h2 style="margin:0;color:#fff;font-size:1.3rem;">🏢 Psikotes Karyawan</h2>
    <p style="margin:6px 0 0;color:#bbdefb;font-size:.9rem;">{tujuan_label} — HRIS SmartDesk</p>
  </div>
  <div style="padding:28px 32px;">
    <p style="color:#424242;">Yth. <strong>{employee.nama}</strong>,</p>
    <p style="color:#424242;font-size:.92rem;line-height:1.6;">
      Anda dijadwalkan untuk mengikuti <strong>psikotes {tujuan_label}</strong>.
    </p>
    <div style="background:#e3f2fd;border-left:4px solid #1565c0;
                border-radius:6px;padding:16px 20px;margin:20px 0;">
      <table style="width:100%;font-size:.88rem;color:#424242;border-collapse:collapse;">
        <tr><td style="padding:4px 0;width:90px;color:#888;">Paket</td>
            <td style="font-weight:600;">{paket_label}</td></tr>
        <tr><td style="padding:4px 0;color:#888;">Tujuan</td>
            <td style="font-weight:600;">{tujuan_label}</td></tr>
        <tr><td style="padding:4px 0;color:#888;">Berlaku s/d</td>
            <td style="font-weight:600;">{expired_str}</td></tr>
      </table>
    </div>
    <div style="text-align:center;margin:28px 0;">
      <a href="{link}"
         style="background:#1565c0;color:#fff;text-decoration:none;
                padding:14px 36px;border-radius:8px;font-weight:700;
                font-size:1rem;display:inline-block;">
        ▶ Mulai Psikotes
      </a>
    </div>
    <p style="color:#888;font-size:.82rem;">
      Link: <a href="{link}" style="color:#1565c0;">{link}</a>
    </p>
  </div>
  <div style="background:#f5f5f5;padding:16px 32px;text-align:center;font-size:.8rem;color:#aaa;">
    Email otomatis HRIS SmartDesk — jangan balas email ini.
  </div>
</div>
</body>
</html>
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(
            f'Gagal kirim email sesi karyawan ke {email}: {e}'
        )
        return False
