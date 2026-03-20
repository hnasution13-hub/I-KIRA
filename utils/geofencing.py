"""
utils/geofencing.py
Validasi radius check-in karyawan berdasarkan GPS.
"""
import math


def hitung_jarak_meter(lat1, lon1, lat2, lon2):
    """
    Hitung jarak antara dua koordinat GPS menggunakan Haversine formula.
    Return jarak dalam meter (float).
    """
    R = 6_371_000  # radius bumi dalam meter

    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlam = math.radians(float(lon2) - float(lon1))

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 1)


def get_lokasi_referensi(emp):
    """
    Ambil koordinat & radius referensi untuk karyawan.
    Prioritas: JobSite karyawan → Company karyawan.
    Return (lat, lng, radius_meter, sumber) atau (None, None, None, None).
    """
    # Cek JobSite dulu
    job_site = getattr(emp, 'job_site', None)
    if job_site and job_site.latitude and job_site.longitude and job_site.radius_meter:
        return (
            job_site.latitude,
            job_site.longitude,
            job_site.radius_meter,
            f'Job Site: {job_site.nama}',
        )

    # Fallback ke Company
    company = getattr(emp, 'company', None)
    if company and company.latitude and company.longitude and company.radius_meter:
        return (
            company.latitude,
            company.longitude,
            company.radius_meter,
            f'Kantor: {company.nama}',
        )

    return None, None, None, None


def validasi_radius(emp, latitude, longitude):
    """
    Validasi apakah koordinat karyawan dalam radius yang diizinkan.

    Return dict:
    {
        'valid': bool,
        'jarak_meter': float atau None,
        'radius_meter': int atau None,
        'sumber': str,
        'pesan': str,  # pesan untuk ditampilkan ke karyawan
        'pesan_hr': str,  # pesan untuk log HR
    }
    """
    # GPS tidak dikirim
    if latitude is None or longitude is None:
        return {
            'valid': False,
            'jarak_meter': None,
            'radius_meter': None,
            'sumber': '-',
            'pesan': 'Check-in ditolak: GPS tidak aktif. Aktifkan izin lokasi dan coba lagi.',
            'pesan_hr': 'GPS tidak tersedia saat check-in',
        }

    ref_lat, ref_lng, radius, sumber = get_lokasi_referensi(emp)

    # Radius belum diset HR
    if ref_lat is None:
        return {
            'valid': False,
            'jarak_meter': None,
            'radius_meter': None,
            'sumber': '-',
            'pesan': 'Check-in belum dapat dilakukan. HR belum mengatur lokasi kantor. Hubungi HR.',
            'pesan_hr': 'Lokasi kantor/job site belum diset — radius tidak dapat divalidasi',
        }

    jarak = hitung_jarak_meter(latitude, longitude, ref_lat, ref_lng)
    dalam_radius = jarak <= radius

    if dalam_radius:
        return {
            'valid': True,
            'jarak_meter': jarak,
            'radius_meter': radius,
            'sumber': sumber,
            'pesan': '',
            'pesan_hr': f'Dalam radius ({jarak}m dari {sumber})',
        }
    else:
        return {
            'valid': False,
            'jarak_meter': jarak,
            'radius_meter': radius,
            'sumber': sumber,
            'pesan': (
                f'Check-in ditolak: Anda berada {jarak:.0f} meter dari {sumber} '
                f'(radius maksimal {radius} meter). '
                f'Pastikan Anda berada di lokasi kerja.'
            ),
            'pesan_hr': f'Di luar radius: {jarak}m dari {sumber} (maks {radius}m)',
        }
