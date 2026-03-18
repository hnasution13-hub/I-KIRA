"""
apps/registration/views.py
===========================
Self-service registrasi akun Demo & Trial i-Kira.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods
from django.conf import settings
import uuid


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_slug(nama_company):
    base = slugify(nama_company)[:60] or 'company'
    from apps.core.models import Company
    slug = base
    counter = 1
    while Company.objects.filter(slug=slug).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


def _generate_username(nama_company):
    base = slugify(nama_company).replace('-', '')[:12] or 'admin'
    from apps.core.models import User
    username = f'admin.{base}'
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'admin.{base}{counter}'
        counter += 1
    return username


def _hitung_trial_sampai(durasi_hari=30):
    return timezone.now().date() + timezone.timedelta(days=durasi_hari)


# ── Views ─────────────────────────────────────────────────────────────────────

def register_landing(request):
    """Halaman pilihan: Demo atau Trial."""
    return render(request, 'registration/register_landing.html')


@require_http_methods(['GET', 'POST'])
def register_demo(request):
    """Form registrasi akun Demo."""
    if request.method == 'POST':
        return _process_registration(request, paket='demo')
    return render(request, 'registration/register_form.html', {'paket': 'demo'})


@require_http_methods(['GET', 'POST'])
def register_trial(request):
    """Form registrasi akun Trial."""
    if request.method == 'POST':
        return _process_registration(request, paket='trial')
    return render(request, 'registration/register_form.html', {'paket': 'trial'})


def register_success(request):
    """Halaman sukses setelah registrasi."""
    info = request.session.pop('reg_success_info', None)
    if not info:
        return redirect('registration:landing')
    return render(request, 'registration/register_success.html', {'info': info})


def upgrade_page(request):
    """Halaman upgrade — ditampilkan saat trial expired."""
    company = getattr(request, 'company', None)
    return render(request, 'registration/upgrade.html', {
        'company':     company,
        'SALES_WA':    settings.SALES_WA,
        'SALES_EMAIL': settings.SALES_EMAIL,
    })


# ── Core processor ────────────────────────────────────────────────────────────

def _process_registration(request, paket):
    from apps.core.models import Company, User, Department, Position
    from apps.employees.models import PointOfHire, JobSite

    nama_company = request.POST.get('nama_company', '').strip()
    pic_nama     = request.POST.get('pic_nama', '').strip()
    pic_email    = request.POST.get('pic_email', '').strip()
    pic_no_hp    = request.POST.get('pic_no_hp', '').strip()

    # Validasi
    errors = []
    if not nama_company:
        errors.append('Nama perusahaan wajib diisi.')
    if not pic_nama:
        errors.append('Nama PIC wajib diisi.')
    if not pic_email:
        errors.append('Email PIC wajib diisi.')
    if not pic_no_hp:
        errors.append('Nomor HP wajib diisi.')
    if pic_email and User.objects.filter(email=pic_email).exists():
        errors.append('Email sudah terdaftar. Gunakan email lain.')

    if errors:
        for e in errors:
            messages.error(request, e)
        return render(request, 'registration/register_form.html', {
            'paket': paket,
            'post':  request.POST,
        })

    # Buat Company
    slug = _generate_slug(nama_company)
    trial_sampai = None
    if paket == 'trial':
        durasi = getattr(settings, 'TRIAL_DURASI_HARI', 30)
        trial_sampai = _hitung_trial_sampai(durasi)

    company = Company.objects.create(
        nama        = nama_company,
        slug        = slug,
        email       = pic_email,
        status      = paket,           # 'demo' atau 'trial'
        trial_sampai = trial_sampai,
        pic_nama    = pic_nama,
        pic_no_hp   = pic_no_hp,
        demo_reset_schedule = 'daily',
        # Aktifkan semua add-on untuk demo/trial
        addon_assets              = True,
        addon_recruitment         = True,
        addon_psychotest          = True,
        addon_advanced_psychotest = True,
        addon_od                  = True,
    )

    # Buat User Administrator
    username = _generate_username(nama_company)
    password = _generate_password()
    user = User.objects.create(
        username   = username,
        email      = pic_email,
        first_name = pic_nama,
        company    = company,
        role       = 'administrator',
        is_staff   = False,
    )
    user.set_password(password)
    user.save()

    # Seed data master minimal
    _seed_master_minimal(company)

    # Seed data demo jika paket demo
    if paket == 'demo':
        try:
            from apps.registration.demo_seed import seed_demo_data
            seed_demo_data(company)
        except Exception:
            pass  # Jangan gagalkan registrasi karena seed error

    # Kirim email notif
    _send_welcome_email(pic_email, pic_nama, username, password, paket, company, trial_sampai)

    # Simpan info ke session untuk halaman sukses
    request.session['reg_success_info'] = {
        'paket'       : paket,
        'nama_company': nama_company,
        'username'    : username,
        'password'    : password,
        'email'       : pic_email,
        'trial_sampai': str(trial_sampai) if trial_sampai else None,
    }

    # Auto-login user langsung setelah registrasi
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    auth_login(request, user)

    # Tampilkan halaman sukses dulu (user sudah login, tombol → langsung ke dashboard)
    return redirect('registration:success')


def _generate_password():
    """Generate password acak 10 karakter."""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + '!@#$'
    return ''.join(secrets.choice(alphabet) for _ in range(10))


def _seed_master_minimal(company):
    """Buat data master minimal agar sistem tidak error saat login."""
    from apps.core.models import Department, Position
    from apps.employees.models import PointOfHire, JobSite

    dept, _ = Department.objects.get_or_create(
        company=company, nama='Human Resources',
        defaults={'aktif': True}
    )
    Position.objects.get_or_create(
        company=company, nama='Administrator',
        defaults={'level': 'Manager', 'aktif': True, 'department': dept}
    )
    PointOfHire.objects.get_or_create(
        company=company, nama='Pusat',
        defaults={'aktif': True}
    )
    JobSite.objects.get_or_create(
        company=company, nama='Kantor Pusat',
        defaults={'aktif': True}
    )


def _send_welcome_email(email, nama, username, password, paket, company, trial_sampai):
    """Kirim email selamat datang dengan kredensial login."""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    paket_label = 'Demo' if paket == 'demo' else 'Trial'
    subject = f'[i-Kira] Akun {paket_label} Anda Siap!'

    body = render_to_string('registration/email_welcome.html', {
        'nama'        : nama,
        'username'    : username,
        'password'    : password,
        'paket'       : paket_label,
        'company'     : company,
        'trial_sampai': trial_sampai,
        'login_url'   : getattr(settings, 'SITE_URL', 'http://localhost:8000') + '/login/',
    })

    try:
        send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [email],
                  html_message=body, fail_silently=True)
    except Exception:
        pass  # Jangan gagalkan registrasi karena email error
