"""
Email sender utility untuk i-Kira
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_leave_notification(leave, action='submitted'):
    """
    Kirim notifikasi email untuk pengajuan atau persetujuan cuti.
    action: 'submitted' | 'approved' | 'rejected'
    """
    subject_map = {
        'submitted': f'[HRIS] Pengajuan Cuti Baru - {leave.employee.nama}',
        'approved': f'[HRIS] Cuti Anda Disetujui - {leave.tipe_cuti}',
        'rejected': f'[HRIS] Cuti Anda Ditolak - {leave.tipe_cuti}',
    }
    template_map = {
        'submitted': 'emails/leave_submitted.html',
        'approved': 'emails/leave_approved.html',
        'rejected': 'emails/leave_rejected.html',
    }
    subject = subject_map.get(action, '[HRIS] Notifikasi Cuti')
    template = template_map.get(action, 'emails/leave_submitted.html')

    context = {
        'leave': leave,
        'employee': leave.employee,
        'app_name': getattr(settings, 'APP_NAME', 'i-Kira'),
    }

    recipient = []
    if action == 'submitted':
        hr_emails = getattr(settings, 'HR_EMAIL_LIST', [])
        recipient = hr_emails
    else:
        if leave.employee.email:
            recipient = [leave.employee.email]

    if not recipient:
        logger.warning(f"No recipient for leave email (action={action}, leave_id={leave.pk})")
        return False

    try:
        html_content = render_to_string(template, context)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=f"Notifikasi cuti untuk {leave.employee.nama}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info(f"Leave email sent: action={action}, to={recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send leave email: {e}")
        return False


def send_contract_expiry_warning(contract, days_remaining):
    """Kirim peringatan kontrak hampir berakhir ke HR."""
    subject = f'[HRIS] Peringatan: Kontrak {contract.employee.nama} Berakhir {days_remaining} Hari Lagi'
    hr_emails = getattr(settings, 'HR_EMAIL_LIST', [])
    if not hr_emails:
        return False

    try:
        body = (
            f"Kontrak karyawan {contract.employee.nama} ({contract.employee.nik})\n"
            f"No. Kontrak: {contract.nomor_kontrak}\n"
            f"Tipe: {contract.tipe_kontrak}\n"
            f"Berakhir: {contract.tanggal_selesai}\n"
            f"Sisa: {days_remaining} hari\n\n"
            f"Segera lakukan tindak lanjut (perpanjang/terminasi)."
        )
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, hr_emails)
        return True
    except Exception as e:
        logger.error(f"Failed to send contract expiry email: {e}")
        return False


def send_payslip_email(payroll_detail):
    """Kirim slip gaji ke email karyawan dengan template HTML."""
    employee = payroll_detail.employee
    if not employee.email:
        logger.warning(f"send_payslip_email: employee {employee.nik} tidak punya email")
        return False

    subject = f'[HRIS] Slip Gaji {payroll_detail.payroll.periode} - {employee.nama}'
    context = {
        'employee': employee,
        'payroll_detail': payroll_detail,
        'app_name': getattr(settings, 'APP_NAME', 'i-Kira'),
    }
    try:
        html_content = render_to_string('emails/payslip_notification.html', context)
        plain_body = (
            f"Yth. {employee.nama},\n\n"
            f"Slip gaji periode {payroll_detail.payroll.periode} telah tersedia.\n"
            f"Gaji Bersih: Rp {payroll_detail.gaji_bersih:,.0f}\n\n"
            f"Login ke i-Kira untuk melihat detail lengkap.\n\n"
            f"Salam,\nTim HR"
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[employee.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info(f"Payslip email sent to {employee.email} (periode={payroll_detail.payroll.periode})")
        return True
    except Exception as e:
        logger.error(f"Failed to send payslip email to {employee.email}: {e}")
        return False


def send_simple_email(subject, body, recipient_list):
    """Kirim email sederhana."""
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipient_list)
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
