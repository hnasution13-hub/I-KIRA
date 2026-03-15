"""
Management command: python manage.py setup_client --company <slug>
Setup awal data master untuk client baru (departemen, jabatan, POH, job site, perusahaan outsourcing).

Contoh:
    python manage.py setup_client --company pt-maju-jaya
    python manage.py setup_client --company pt-maju-jaya --dry-run

PENTING: --company wajib diisi dengan slug Company yang sudah ada di database.
Buat Company terlebih dahulu via Django Admin sebelum menjalankan command ini.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


# ─────────────────────────────────────────────────────────────
#  EDIT BAGIAN INI SESUAI CLIENT
# ─────────────────────────────────────────────────────────────

DEPARTEMEN = [
    "HSE", "Civil", "Internal Safeguard", "Electricity & Water Facility",
    "General Services", "Garage", "Human Resources", "Logistic",
    "General Affair", "Humas", "Legal", "IT", "KTT", "Mixing Plant",
    "FAT", "Purchasing", "Mining",
]

JABATAN = [
    "Safety Officer", "Foreman Cum Humas", "Safeguard", "Chief Safeguard",
    "Leader", "Helper Kitchen", "Crew (Safetyman)", "Helper Waterman",
    "Helper Mechanic", "Foreman Mechanic", "Junior Leader", "Mechanic",
    "HR Senior Officer", "Cleaning Service Cum Driver GS", "Senior Leader",
    "Operator Genset", "Driver LV/Truck", "Foreman Safety", "Assistant Manager",
    "Clerk Admin HSE", "Supervisor GA", "IT Assistant Manager",
    "Foreman Mechanic AC", "Clerk Admin (Mechanic)", "Site Interpreter",
    "Carpenter", "Helper Logistic", "Technician", "Clerk Admin GA",
    "Electric Officer", "Crew Nursery Garden", "ABK Kapal", "Advisor",
    "Office Girl", "Manager CHP", "Cleark Admin Civil", "Operator ADT",
    "Operator Dozer", "Operator DT", "Operator Excavator", "Operator Grader",
    "Operator Loader", "Checker", "Welder", "Foreman HE Mechanic", "IT Officer",
    "HSE Officer", "KTT", "Cleark Admin Legal", "Staff KTT",
    "Site Interpreter/Admin", "GS Officer Cum Translater", "Finance Officer",
    "Admin cum Translator", "Purchasing Officer", "Accounting Specialist",
    "Legal Officer", "Personil Pemadam", "Surveyor", "Manager HR",
    "Admin Logistic Cum Translator", "Analis Lab (Teknisi Lab)",
    "HR Admin Cum Translator", "Crew Safety Man", "Maintenance & AC",
    "Admin Lab", "Preparasi", "Admin GA Cum Translator",
]

POINT_OF_HIRE = [
    "Riau", "Laroenai", "Surabaya", "Tarakan", "Saulu", "Jakarta",
    "Jogjakarta", "Mamuju", "Pontianak", "Medan", "Batam", "Jambi",
    "Kendari", "Buleleng", "Bandung", "Pekanbaru", "Makassar", "Manado",
    "Malang", "Palembang", "Samarinda", "Denpasar", "Banggai", "Lampung",
    "Singkawang", "Gowa",
]

JOB_SITE = [
    "Site Laroenai",
]

PERUSAHAAN_OUTSOURCING = [
    "Transon Bumindo Resources",
]

# ─────────────────────────────────────────────────────────────


class Command(BaseCommand):
    help = 'Setup awal data master untuk client baru. Wajib --company <slug>.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            required=True,
            help='Slug Company yang sudah terdaftar. Contoh: --company pt-maju-jaya',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview data yang akan diimport tanpa menyimpan ke database',
        )

    def handle(self, *args, **options):
        from apps.core.models import Company, Department, Position
        from apps.employees.models import PointOfHire, JobSite, Perusahaan

        dry_run      = options['dry_run']
        company_slug = options['company']

        # Validasi company
        try:
            company = Company.objects.get(slug=company_slug)
        except Company.DoesNotExist:
            raise CommandError(
                f'Company dengan slug "{company_slug}" tidak ditemukan.\n'
                f'Buat Company terlebih dahulu via Django Admin (/admin/).'
            )

        self.stdout.write(self.style.SUCCESS(f'\nSetup untuk: {company.nama} [{company.slug}]'))
        if dry_run:
            self.stdout.write(self.style.WARNING('*** DRY RUN — tidak ada yang disimpan ***\n'))

        tasks = [
            ('DEPARTEMEN',             Department,  DEPARTEMEN,             {'company': company}),
            ('JABATAN',                Position,    JABATAN,                {'company': company}),
            ('POINT OF HIRE',          PointOfHire, POINT_OF_HIRE,          {'company': company}),
            ('JOB SITE',               JobSite,     JOB_SITE,               {'company': company}),
            ('PERUSAHAAN OUTSOURCING', Perusahaan,  PERUSAHAAN_OUTSOURCING,  {'company': company}),
        ]

        total_created = 0
        total_skipped = 0

        for label, Model, data_list, extra_fields in tasks:
            if not data_list:
                self.stdout.write(f'\n── {label}: (kosong, dilewati)')
                continue

            self.stdout.write(f'\n── {label} ──────────────────────────')

            seen   = set()
            unique = []
            for nama in data_list:
                nama = nama.strip()
                if nama and nama.lower() not in seen:
                    seen.add(nama.lower())
                    unique.append(nama)

            created = skipped = 0
            for nama in unique:
                exists = Model.objects.filter(nama__iexact=nama, company=company).exists()
                if exists:
                    skipped += 1
                    self.stdout.write(f'  ⏭  {nama}')
                else:
                    created += 1
                    self.stdout.write(f'  ✅ {nama}')
                    if not dry_run:
                        Model.objects.create(nama=nama, aktif=True, **extra_fields)

            self.stdout.write(f'   → {created} ditambahkan, {skipped} sudah ada')
            total_created += created
            total_skipped += skipped

        self.stdout.write('')

        # Buat user Administrator untuk company ini jika belum ada
        from apps.core.models import User
        has_admin = User.objects.filter(company=company, role='administrator').exists()
        if not has_admin and not dry_run:
            self.stdout.write(self.style.WARNING(
                f'\n⚠  Belum ada user Administrator untuk {company.nama}.\n'
                f'   Buat via Django Admin: /admin/core/user/add/\n'
                f'   Set role = "administrator" dan company = {company.nama}'
            ))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN selesai. {total_created} akan ditambahkan, {total_skipped} sudah ada.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Setup selesai! {total_created} data ditambahkan, {total_skipped} sudah ada.'
            ))
