"""
Validator functions untuk i-Kira
"""
import re
from django.core.exceptions import ValidationError


def validate_nik(value):
    """NIK karyawan: 3-20 karakter alphanumeric"""
    if not re.match(r'^[A-Z0-9\-]{3,20}$', value.upper()):
        raise ValidationError('NIK harus 3-20 karakter (huruf, angka, atau tanda hubung).')


def validate_no_ktp(value):
    """No KTP: 16 digit angka"""
    if value and not re.match(r'^\d{16}$', value):
        raise ValidationError('No. KTP harus 16 digit angka.')


def validate_no_npwp(value):
    """No NPWP: format XX.XXX.XXX.X-XXX.XXX"""
    if value:
        cleaned = re.sub(r'[\.\-]', '', value)
        if not re.match(r'^\d{15}$', cleaned):
            raise ValidationError('No. NPWP tidak valid. Format: XX.XXX.XXX.X-XXX.XXX')


def validate_no_hp(value):
    """No HP: 10-15 digit, boleh diawali +62"""
    if value:
        cleaned = re.sub(r'[\s\-\+]', '', value)
        if not re.match(r'^(62|0)\d{8,13}$', cleaned):
            raise ValidationError('No. HP tidak valid. Contoh: 08123456789 atau +6281234567890')


def validate_gaji_positif(value):
    """Gaji harus lebih dari 0"""
    if value is not None and value < 0:
        raise ValidationError('Nominal tidak boleh negatif.')


def validate_jam_lembur(value):
    """Jam lembur: 0 - 14 jam per hari"""
    if value is not None and (value < 0 or value > 14):
        raise ValidationError('Jam lembur tidak valid (0-14 jam).')


def validate_file_size(file, max_mb=5):
    """Validasi ukuran file maksimal N MB"""
    if file and file.size > max_mb * 1024 * 1024:
        raise ValidationError(f'Ukuran file maksimal {max_mb} MB.')


def validate_image_extension(value):
    """Validasi ekstensi file gambar"""
    valid_ext = ['.jpg', '.jpeg', '.png', '.webp']
    import os
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_ext:
        raise ValidationError(f'File harus berformat: {", ".join(valid_ext)}')


def validate_dokumen_extension(value):
    """Validasi ekstensi dokumen"""
    valid_ext = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    import os
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_ext:
        raise ValidationError(f'File harus berformat: {", ".join(valid_ext)}')


def validate_periode_payroll(value):
    """Periode payroll format YYYY-MM"""
    if not re.match(r'^\d{4}-(0[1-9]|1[0-2])$', value):
        raise ValidationError('Format periode tidak valid. Gunakan YYYY-MM (contoh: 2024-01).')
