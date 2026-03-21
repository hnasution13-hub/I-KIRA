from django.db import models
from django.contrib.auth.models import AbstractUser


# ══════════════════════════════════════════════════════════════════════════════
#  COMPANY — Tenant Utama
# ══════════════════════════════════════════════════════════════════════════════

class Company(models.Model):
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('trial',    'Trial'),
        ('demo',     'Demo'),
        ('suspend',  'Suspend'),
        ('nonaktif', 'Nonaktif'),
    ]
    DEMO_RESET_CHOICES = [
        ('daily',  'Setiap Hari (00:00)'),
        ('weekly', 'Setiap Minggu (Senin 00:00)'),
    ]
    nama           = models.CharField(max_length=200, verbose_name='Nama Perusahaan')
    singkatan      = models.CharField(max_length=20, blank=True, verbose_name='Singkatan')
    slug           = models.SlugField(max_length=80, unique=True, verbose_name='Slug',
                                      help_text='Identifier unik. Contoh: pt-maju-jaya')
    npwp           = models.CharField(max_length=25, blank=True, verbose_name='NPWP')
    alamat         = models.TextField(blank=True, verbose_name='Alamat')
    no_telp        = models.CharField(max_length=20, blank=True, verbose_name='No. Telepon')
    email          = models.EmailField(blank=True, verbose_name='Email')
    website        = models.URLField(blank=True, verbose_name='Website')
    logo           = models.ImageField(upload_to='company_logos/', null=True, blank=True, verbose_name='Logo')
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='trial')
    tanggal_daftar = models.DateField(auto_now_add=True, verbose_name='Tanggal Daftar')
    trial_sampai   = models.DateField(null=True, blank=True, verbose_name='Trial Sampai')
    catatan        = models.TextField(blank=True, verbose_name='Catatan Internal')

    # ── Demo & Trial ──────────────────────────────────────────────────────────
    demo_reset_schedule = models.CharField(
        max_length=10, choices=DEMO_RESET_CHOICES, default='daily',
        verbose_name='Jadwal Reset Demo',
        help_text='Hanya berlaku jika status = Demo',
    )
    last_demo_reset = models.DateTimeField(null=True, blank=True, verbose_name='Terakhir Reset Demo')
    pic_nama        = models.CharField(max_length=100, blank=True, verbose_name='Nama PIC')
    pic_no_hp       = models.CharField(max_length=20, blank=True, verbose_name='No HP / WhatsApp PIC')

    # ── Paket Langganan ───────────────────────────────────────────────────────
    PAKET_CHOICES = [
        ('starter',      'Starter (s/d 100 karyawan)'),
        ('professional', 'Professional (s/d 300 karyawan)'),
        ('pro_full',     'Pro Full (s/d 500 karyawan)'),
        ('enterprise',   'Enterprise (Unlimited)'),
    ]
    PAKET_LIMIT = {
        'starter':      100,
        'professional': 300,
        'pro_full':     500,
        'enterprise':   999999,
    }
    PAKET_HARGA = {
        'starter':      1_499_000,
        'professional': 2_999_000,
        'pro_full':     3_499_000,
        'enterprise':   0,  # nego
    }
    paket = models.CharField(
        max_length=20, choices=PAKET_CHOICES, default='starter',
        verbose_name='Paket Langganan',
        help_text='Paket yang diambil oleh tenant ini'
    )
    enforce_limit = models.BooleanField(
        default=False,
        verbose_name='Aktifkan Batas Karyawan',
        help_text='OFF = unlimited (untuk testing/demo). ON = batas karyawan berlaku sesuai paket.'
    )

    # ── Add-On Flags ──────────────────────────────────────────────────────────
    addon_assets              = models.BooleanField(default=False, verbose_name='Add-On: Asset Management')
    addon_recruitment         = models.BooleanField(default=False, verbose_name='Add-On: Rekrutmen')
    addon_psychotest          = models.BooleanField(default=False, verbose_name='Add-On: Psikotes')
    addon_advanced_psychotest = models.BooleanField(default=False, verbose_name='Add-On: Advanced Psychotest (OCEAN)')
    addon_od                  = models.BooleanField(default=False, verbose_name='Add-On: Organisation Development')
    addon_performance         = models.BooleanField(default=False, verbose_name='Add-On: Performance & KPI')

    # ── Penandatangan Default ─────────────────────────────────────────────────
    nama_penandatangan_default    = models.CharField(max_length=100, blank=True,
                                                      verbose_name='Nama Penandatangan Default')
    jabatan_penandatangan_default = models.CharField(max_length=100, blank=True,
                                                      verbose_name='Jabatan Penandatangan Default')

    # ── Geofencing (fallback jika JobSite tidak diset) ────────────────────────
    latitude     = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True, verbose_name='Latitude Kantor Pusat'
    )
    longitude    = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True, verbose_name='Longitude Kantor Pusat'
    )
    radius_meter = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Radius Check-In Kantor Pusat (meter)',
        help_text='Fallback jika Job Site tidak punya koordinat.'
    )

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Perusahaan (Tenant)'
        verbose_name_plural = 'Perusahaan (Tenant)'
        ordering            = ['nama']

    def __str__(self):
        return f'{self.nama} [{self.status.upper()}]'

    @property
    def is_aktif(self):
        from django.utils import timezone
        if self.status == 'aktif':
            return True
        if self.status == 'demo':
            return True
        if self.status == 'trial' and self.trial_sampai:
            return timezone.now().date() <= self.trial_sampai
        return False

    @property
    def is_trial_expired(self):
        from django.utils import timezone
        if self.status == 'trial' and self.trial_sampai:
            return timezone.now().date() > self.trial_sampai
        return False

    @property
    def trial_sisa_hari(self):
        from django.utils import timezone
        if self.status == 'trial' and self.trial_sampai:
            delta = self.trial_sampai - timezone.now().date()
            return max(delta.days, 0)
        return None

    # ── Paket & Kapasitas ─────────────────────────────────────────────────────

    @property
    def paket_limit_karyawan(self):
        """Batas maksimal karyawan sesuai paket."""
        return self.PAKET_LIMIT.get(self.paket, 100)

    @property
    def jumlah_karyawan_aktif(self):
        """Hitung karyawan aktif real-time dari database."""
        try:
            from apps.employees.models import Employee
            return Employee.objects.filter(company=self, status='Aktif').count()
        except Exception:
            return 0

    @property
    def persen_kapasitas(self):
        """Persentase penggunaan kapasitas (0-100). Hanya relevan kalau enforce_limit=True."""
        if not self.enforce_limit or self.paket == 'enterprise':
            return 0
        limit = self.paket_limit_karyawan
        return min(round(self.jumlah_karyawan_aktif / limit * 100, 1), 100)

    @property
    def sisa_kuota_karyawan(self):
        """Sisa slot karyawan. Unlimited kalau enforce_limit=False atau enterprise."""
        if not self.enforce_limit or self.paket == 'enterprise':
            return 999999
        return max(self.paket_limit_karyawan - self.jumlah_karyawan_aktif, 0)

    @property
    def notif_kapasitas(self):
        """
        Level notifikasi kapasitas karyawan.
        None     = aman / limit tidak aktif
        warning  = >= 90% (kurang sedikit dari batas)
        critical = >= 95% (hampir penuh)
        full     = >= 100% (sudah penuh)
        Hanya aktif kalau enforce_limit = True.
        """
        if not self.enforce_limit or self.paket == 'enterprise':
            return None
        pct = self.persen_kapasitas
        if pct >= 100:
            return 'full'
        elif pct >= 95:
            return 'critical'
        elif pct >= 90:
            return 'warning'
        return None

    @property
    def harga_paket(self):
        """Harga paket bulanan (Rp). Enterprise = 0 karena nego."""
        return self.PAKET_HARGA.get(self.paket, 0)

    @property
    def harga_addon_aktif(self):
        """Total harga addon yang aktif (Rp)."""
        ADDON_HARGA = {
            'addon_advanced_psychotest': 249_000,
            'addon_assets':             199_000,
            'addon_od':                 299_000,
            'addon_performance':        299_000,
        }
        total = 0
        for field, harga in ADDON_HARGA.items():
            if getattr(self, field, False):
                total += harga
        return total

    @property
    def total_tagihan_bulanan(self):
        """Total tagihan bulanan = harga paket + semua addon aktif."""
        return self.harga_paket + self.harga_addon_aktif

    @property
    def detail_tagihan(self):
        """
        Detail breakdown tagihan untuk ditampilkan ke client atau kalkulasi revenue.
        Return dict berisi item-item tagihan.
        """
        ADDON_LABEL = {
            'addon_advanced_psychotest': ('Psikotes Advance', 249_000),
            'addon_assets':              ('Asset Management', 199_000),
            'addon_od':                  ('OD & Kompetensi', 299_000),
            'addon_performance':         ('Performance & KPI', 299_000),
        }
        items = []
        items.append({
            'label': f'Paket {self.get_paket_display()}',
            'harga': self.harga_paket,
            'tipe':  'paket',
        })
        for field, (label, harga) in ADDON_LABEL.items():
            if getattr(self, field, False):
                items.append({
                    'label': f'Add-On: {label}',
                    'harga': harga,
                    'tipe':  'addon',
                })
        return {
            'items': items,
            'total': self.total_tagihan_bulanan,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  DEPARTMENT & POSITION — Per Company
# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
#  ADDON LICENSE
# ══════════════════════════════════════════════════════════════════════════════

class AddonLicense(models.Model):
    """Lisensi per addon per company. Diaktifkan via serial key HMAC offline."""
    ADDON_CHOICES = [
        ('assets',              'Asset Management'),
        ('recruitment',         'Rekrutmen'),
        ('psychotest',          'Psikotes'),
        ('advanced_psychotest', 'Advanced Psychotest (OCEAN)'),
        ('od',                  'Organisation Development'),
    ]
    company         = models.ForeignKey('Company', on_delete=models.CASCADE,
                                         related_name='addon_licenses')
    addon           = models.CharField(max_length=30, choices=ADDON_CHOICES)
    serial_key      = models.CharField(max_length=100, verbose_name='Serial Key')
    expiry          = models.DateField(null=True, blank=True,
                                        verbose_name='Tanggal Expired',
                                        help_text='NULL = Lifetime')
    aktif           = models.BooleanField(default=True)
    diaktifkan_oleh = models.CharField(max_length=100, blank=True)
    aktif_sejak     = models.DateField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Addon License'
        verbose_name_plural = 'Addon Licenses'
        unique_together     = [['company', 'addon']]
        ordering            = ['company', 'addon']

    def __str__(self):
        exp = self.expiry.strftime('%d/%m/%Y') if self.expiry else 'Lifetime'
        return f'{self.company.nama} — {self.get_addon_display()} ({exp})'

    @property
    def is_valid(self):
        from apps.core.license import GRACE_DAYS
        from datetime import date
        if not self.aktif:
            return False
        if self.expiry is None:
            return True
        return (self.expiry - date.today()).days >= -GRACE_DAYS

    @property
    def is_grace(self):
        from apps.core.license import GRACE_DAYS
        from datetime import date
        if self.expiry is None:
            return False
        d = (self.expiry - date.today()).days
        return -GRACE_DAYS <= d < 0

    @property
    def days_until_expiry(self):
        from datetime import date
        if self.expiry is None:
            return None
        return (self.expiry - date.today()).days



class Department(models.Model):
    company    = models.ForeignKey(Company, on_delete=models.CASCADE,
                                   related_name='departments', verbose_name='Perusahaan')
    nama       = models.CharField(max_length=100, verbose_name='Nama Departemen')
    kode       = models.CharField(max_length=20, blank=True)
    deskripsi  = models.TextField(blank=True)
    aktif      = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Departemen'
        verbose_name_plural = 'Departemen'
        ordering            = ['nama']
        unique_together     = [['company', 'nama']]

    def __str__(self):
        return self.nama


class Position(models.Model):
    LEVEL_CHOICES = [
        ('Crew',                 'Crew'),
        ('Jr.Staff',             'Jr.Staff'),
        ('Staff',                'Staff'),
        ('Sr.Staff',             'Sr.Staff'),
        ('Jr.Supervisor',        'Jr.Supervisor'),
        ('Supervisor',           'Supervisor'),
        ('Sr.Supervisor',        'Sr.Supervisor'),
        ('Jr.Superintendent',    'Jr.Superintendent'),
        ('Superintendent',       'Superintendent'),
        ('Sr.Superintendent',    'Sr.Superintendent'),
        ('Jr.Manager',           'Jr.Manager'),
        ('Manager',              'Manager'),
        ('Sr.Manager',           'Sr.Manager'),
        ('Manajemen',            'Manajemen'),
        ('Corporate Manajemen',  'Corporate Manajemen'),
    ]
    PENDIDIKAN_CHOICES = [
        ('', 'Tidak Ditentukan'), ('SD', 'SD'), ('SMP', 'SMP'),
        ('SMA/SMK', 'SMA/SMK'), ('D3', 'D3'), ('S1', 'S1'), ('S2', 'S2'), ('S3', 'S3'),
    ]

    company              = models.ForeignKey(Company, on_delete=models.CASCADE,
                                             related_name='positions', verbose_name='Perusahaan')
    nama                 = models.CharField(max_length=100)
    level                = models.CharField(max_length=50, choices=LEVEL_CHOICES, default='Staff')
    department           = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    deskripsi            = models.TextField(blank=True, verbose_name='Deskripsi Jabatan')
    aktif                = models.BooleanField(default=True)
    created_at           = models.DateTimeField(auto_now_add=True)
    job_desc             = models.TextField(blank=True, verbose_name='Job Description')
    skill_wajib          = models.TextField(blank=True, verbose_name='Skill Wajib')
    skill_diinginkan     = models.TextField(blank=True, verbose_name='Skill Diinginkan')
    pendidikan_min       = models.CharField(max_length=10, blank=True, choices=PENDIDIKAN_CHOICES, default='')
    pengalaman_min       = models.IntegerField(default=0, verbose_name='Pengalaman Minimum (tahun)')
    bobot_skill_wajib    = models.IntegerField(default=40)
    bobot_pengalaman     = models.IntegerField(default=25)
    bobot_pendidikan     = models.IntegerField(default=20)
    bobot_skill_tambahan = models.IntegerField(default=15)

    # ── NEW: Hierarki Jabatan ─────────────────────────────────────────────────
    parent = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        verbose_name='Atasan Jabatan',
        help_text='Jabatan yang menjadi atasan langsung. Kosong = pucuk hierarki.',
    )

    class Meta:
        verbose_name        = 'Jabatan'
        verbose_name_plural = 'Jabatan'
        ordering            = ['nama']
        unique_together     = [['company', 'nama']]

    def __str__(self):
        return self.nama

    # ── Properti hierarki ────────────────────────────────────────────────────
    def get_ancestors(self):
        """Kembalikan list jabatan dari atas ke bawah hingga jabatan ini (exclusive)."""
        ancestors = []
        current = self.parent
        seen = set()
        while current and current.id not in seen:
            ancestors.insert(0, current)
            seen.add(current.id)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """Kembalikan semua jabatan di bawah jabatan ini (rekursif)."""
        result = []
        for child in self.children.filter(aktif=True):
            result.append(child)
            result.extend(child.get_descendants())
        return result

    def get_approver_for(self, modul: str):
        """
        Resolve approver jabatan untuk modul tertentu.
        Urutan: ApprovalMatrix eksplisit → parent jabatan → None.
        """
        from apps.core.models import ApprovalMatrix
        matrix = ApprovalMatrix.objects.filter(
            company=self.company, modul=modul,
            jabatan_pemohon=self, level_approval=1, aktif=True,
        ).select_related('jabatan_approver').first()
        if matrix and matrix.jabatan_approver:
            return matrix.jabatan_approver
        return self.parent  # fallback ke parent hirarki

    def get_full_approval_chain(self, modul: str):
        """Kembalikan list jabatan approver terurut dari level 1 ke atas."""
        from apps.core.models import ApprovalMatrix
        matrices = ApprovalMatrix.objects.filter(
            company=self.company, modul=modul,
            jabatan_pemohon=self, aktif=True,
        ).order_by('level_approval').select_related('jabatan_approver')

        chain = []
        if matrices.exists():
            for m in matrices:
                if m.jabatan_approver:
                    chain.append({'level': m.level_approval, 'jabatan': m.jabatan_approver,
                                  'auto_approve_hari': m.auto_approve_hari})
        else:
            # Auto-derive dari hierarki
            current = self.parent
            level = 1
            seen = set()
            while current and current.id not in seen:
                chain.append({'level': level, 'jabatan': current, 'auto_approve_hari': 0})
                seen.add(current.id)
                current = current.parent
                level += 1
        return chain

    # ── Properti ATS ─────────────────────────────────────────────────────────
    @property
    def skill_wajib_list(self):
        return [s.strip() for s in self.skill_wajib.split(',') if s.strip()] if self.skill_wajib else []

    @property
    def skill_diinginkan_list(self):
        return [s.strip() for s in self.skill_diinginkan.split(',') if s.strip()] if self.skill_diinginkan else []

    @property
    def total_bobot(self):
        return self.bobot_skill_wajib + self.bobot_pengalaman + self.bobot_pendidikan + self.bobot_skill_tambahan

    @property
    def bobot_valid(self):
        return self.total_bobot == 100

    def clean(self):
        from django.core.exceptions import ValidationError
        total = (
            (self.bobot_skill_wajib or 0) + (self.bobot_pengalaman or 0) +
            (self.bobot_pendidikan or 0) + (self.bobot_skill_tambahan or 0)
        )
        if total != 100:
            raise ValidationError(f'Total bobot ATS harus 100%. Saat ini: {total}%.')

    def get_kriteria_dict(self):
        return {
            'jabatan':          self.nama,
            'pendidikan_min':   self.pendidikan_min,
            'pengalaman_min':   self.pengalaman_min,
            'skill_wajib':      self.skill_wajib_list,
            'skill_diinginkan': self.skill_diinginkan_list,
            'bobot': {
                'skill_wajib':      self.bobot_skill_wajib,
                'pengalaman':       self.bobot_pengalaman,
                'pendidikan':       self.bobot_pendidikan,
                'skill_diinginkan': self.bobot_skill_tambahan,
            }
        }


# ══════════════════════════════════════════════════════════════════════════════
#  ORG CHART — Snapshot visual per periode
# ══════════════════════════════════════════════════════════════════════════════

class OrgChart(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('aktif', 'Aktif'),
        ('arsip', 'Diarsipkan'),
    ]
    company       = models.ForeignKey(Company, on_delete=models.CASCADE,
                                      related_name='org_charts', verbose_name='Perusahaan')
    nama          = models.CharField(max_length=200, verbose_name='Nama Org Chart')
    periode       = models.CharField(max_length=7, verbose_name='Periode (YYYY)')
    berlaku_mulai = models.DateField(verbose_name='Berlaku Mulai')
    berlaku_sampai = models.DateField(null=True, blank=True, verbose_name='Berlaku Sampai')
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    deskripsi     = models.TextField(blank=True)
    created_by    = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='org_charts_created', verbose_name='Dibuat Oleh')
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Org Chart'
        verbose_name_plural = 'Org Charts'
        ordering            = ['-berlaku_mulai']

    def __str__(self):
        return f'{self.nama} ({self.periode})'

    def get_tree_by_department(self):
        """
        Kembalikan dict {dept_nama: [tree_nodes]} untuk render org chart.
        Setiap node: {position, level, children, employee_count, employees}.
        """
        from apps.employees.models import Employee

        positions = Position.objects.filter(
            company=self.company, aktif=True,
        ).select_related('department', 'parent').prefetch_related('children')

        # Group by dept
        dept_trees = {}
        roots_by_dept = {}

        for pos in positions:
            dept_nama = pos.department.nama if pos.department else 'Tanpa Departemen'
            if dept_nama not in roots_by_dept:
                roots_by_dept[dept_nama] = []
            # Cek root per dept: parent kosong, atau parent beda dept
            is_root = (
                pos.parent is None or
                pos.parent.department != pos.department
            )
            if is_root:
                roots_by_dept[dept_nama].append(pos)

        def build_node(pos):
            emp_qs = Employee.objects.filter(
                company=self.company, jabatan=pos, status='Aktif',
            ).select_related()
            return {
                'position': pos,
                'employee_count': emp_qs.count(),
                'employees': list(emp_qs[:5]),  # preview max 5
                'children': [build_node(c) for c in pos.children.filter(aktif=True)],
            }

        for dept_nama, roots in roots_by_dept.items():
            dept_trees[dept_nama] = [build_node(r) for r in roots]

        return dept_trees


# ══════════════════════════════════════════════════════════════════════════════
#  APPROVAL MATRIX — Siapa menyetujui apa
# ══════════════════════════════════════════════════════════════════════════════

class ApprovalMatrix(models.Model):
    MODUL_CHOICES = [
        ('leave',       'Cuti / Izin'),
        ('overtime',    'Lembur'),
        ('payroll',     'Payroll'),
        ('performance', 'Penilaian Kinerja'),
        ('movement',    'Mutasi / Promosi'),
        ('recruitment', 'Rekrutmen / MPP'),
        ('contract',    'Kontrak Kerja'),
        ('sp',          'Surat Peringatan'),
        ('phk',         'Pemutusan Hubungan Kerja'),
    ]

    company            = models.ForeignKey(Company, on_delete=models.CASCADE,
                                           related_name='approval_matrices', verbose_name='Perusahaan')
    modul              = models.CharField(max_length=30, choices=MODUL_CHOICES, verbose_name='Modul')
    jabatan_pemohon    = models.ForeignKey(Position, on_delete=models.CASCADE,
                                           related_name='approval_sebagai_pemohon',
                                           verbose_name='Jabatan Pemohon')
    level_approval     = models.PositiveSmallIntegerField(default=1, verbose_name='Level Approval',
                                                          help_text='1 = approval pertama, dst.')
    jabatan_approver   = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='approval_sebagai_approver',
                                           verbose_name='Jabatan Approver',
                                           help_text='Kosong = auto-derive dari Position.parent.')
    auto_approve_hari  = models.PositiveSmallIntegerField(default=0, verbose_name='Auto-Approve (hari)',
                                                          help_text='0 = tidak auto.')
    notif_email        = models.BooleanField(default=True, verbose_name='Kirim Notif Email')
    aktif              = models.BooleanField(default=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Approval Matrix'
        verbose_name_plural = 'Approval Matrix'
        ordering            = ['modul', 'jabatan_pemohon', 'level_approval']
        unique_together     = [['company', 'modul', 'jabatan_pemohon', 'level_approval']]

    def __str__(self):
        approver = self.jabatan_approver.nama if self.jabatan_approver else '(auto)'
        return f'{self.get_modul_display()} | {self.jabatan_pemohon.nama} → L{self.level_approval}: {approver}'


# ══════════════════════════════════════════════════════════════════════════════
#  USER — Terikat Company
# ══════════════════════════════════════════════════════════════════════════════

class User(AbstractUser):
    ROLE_CHOICES = [
        ('administrator', 'Administrator'),
        ('admin',         'Admin'),
        ('hr_manager',    'HR Manager'),
        ('hr_staff',      'HR Staff'),
        ('manager',       'Manager'),
        ('employee',      'Employee'),
    ]
    company       = models.ForeignKey(Company, on_delete=models.SET_NULL,
                                      null=True, blank=True,
                                      related_name='users', verbose_name='Perusahaan')
    nik           = models.CharField(max_length=20, null=True, blank=True, verbose_name='NIK')
    role          = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    department    = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    jabatan       = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    no_hp         = models.CharField(max_length=20, blank=True)
    foto          = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name        = 'User'
        verbose_name_plural = 'Users'

    def get_full_name(self):
        full = super().get_full_name().strip()
        return full or self.username

    def __str__(self):
        co = f' [{self.company.singkatan or self.company.nama}]' if self.company else ' [DEV]'
        return f'{self.get_full_name() or self.username}{co}'

    @property
    def is_developer(self):
        return self.is_superuser and self.company is None

    @property
    def is_administrator(self):
        return self.role == 'administrator' and self.company is not None

    @property
    def is_hr(self):
        return self.role in ['administrator', 'admin', 'hr_manager', 'hr_staff']

    @property
    def is_manager_level(self):
        return self.role in ['administrator', 'admin', 'hr_manager', 'manager']

    @property
    def is_superadmin(self):
        return self.is_developer

    # ── Helper: resolve approver untuk user ini ───────────────────────────────
    def get_approver_employee(self, modul: str):
        """
        Kembalikan Employee pertama yang menjabat sebagai approver untuk modul ini.
        Resolve dari ApprovalMatrix → fallback ke jabatan parent → fallback ke atasan HR.
        """
        from apps.employees.models import Employee
        if not self.jabatan:
            return None
        approver_pos = self.jabatan.get_approver_for(modul)
        if approver_pos:
            return Employee.objects.filter(
                company=self.company, jabatan=approver_pos, status='Aktif',
            ).first()
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  AUDIT LOG — Per Company
# ══════════════════════════════════════════════════════════════════════════════

class AuditLog(models.Model):
    company    = models.ForeignKey(Company, on_delete=models.CASCADE,
                                   null=True, blank=True, verbose_name='Perusahaan')
    user       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action     = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    object_id  = models.IntegerField(null=True, blank=True)
    detail     = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering            = ['-timestamp']

    def __str__(self):
        return f'{self.user} - {self.action} - {self.timestamp}'
