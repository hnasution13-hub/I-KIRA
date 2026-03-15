from django.db import models
from django.utils import timezone
from apps.employees.models import Employee
from apps.core.models import Company
from apps.core.models import Department


class Shift(models.Model):
    """
    Master data shift kerja.
    Mendukung 4 tipe: Fixed, Rotating, Split, Flexible.
    """
    TIPE_CHOICES = [
        ('fixed',    'Fixed (jam tetap tiap hari)'),
        ('rotating', 'Rotating (bergantian antar shift)'),
        ('split',    'Split Shift (pagi + malam)'),
        ('flexible', 'Flexible / WFA (bebas, hitung durasi)'),
    ]
    HARI_CHOICES = [
        (0, 'Senin'), (1, 'Selasa'), (2, 'Rabu'),
        (3, 'Kamis'), (4, 'Jumat'), (5, 'Sabtu'), (6, 'Minggu'),
    ]

    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='shifts', verbose_name='Perusahaan')
    nama        = models.CharField(max_length=100, unique=True, verbose_name='Nama Shift')
    kode        = models.CharField(max_length=10, unique=True, verbose_name='Kode Shift',
                                   help_text='Contoh: S1, PAGI, MALAM')
    tipe        = models.CharField(max_length=10, choices=TIPE_CHOICES, default='fixed')
    warna       = models.CharField(max_length=7, default='#0d6efd',
                                   verbose_name='Warna (hex)', help_text='Untuk tampilan roster')
    aktif       = models.BooleanField(default=True)
    keterangan  = models.TextField(blank=True)

    # ── Jam kerja utama ───────────────────────────────────────────────────────
    jam_masuk   = models.TimeField(null=True, blank=True, verbose_name='Jam Masuk')
    jam_keluar  = models.TimeField(null=True, blank=True, verbose_name='Jam Keluar')
    toleransi_telat = models.IntegerField(default=0, verbose_name='Toleransi Telat (menit)',
                                          help_text='Menit keterlambatan yang tidak dihitung')

    # ── Split shift: sesi kedua ───────────────────────────────────────────────
    jam_masuk_2  = models.TimeField(null=True, blank=True, verbose_name='Jam Masuk Sesi 2')
    jam_keluar_2 = models.TimeField(null=True, blank=True, verbose_name='Jam Keluar Sesi 2')

    # ── Flexible: minimal durasi kerja ───────────────────────────────────────
    minimal_jam_kerja = models.DecimalField(max_digits=4, decimal_places=1, default=8,
                                            verbose_name='Minimal Jam Kerja (flexible)')

    # ── Hari kerja aktif (bitmask via M2M-style, simpan sebagai string) ──────
    # Format: "0,1,2,3,4" = Senin–Jumat
    hari_kerja  = models.CharField(max_length=20, default='0,1,2,3,4',
                                   verbose_name='Hari Kerja Aktif',
                                   help_text='0=Senin,1=Selasa,...,6=Minggu. Pisah koma.')

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Shift'
        verbose_name_plural = 'Shift'
        ordering = ['nama']

    def __str__(self):
        return f"{self.kode} — {self.nama}"

    @property
    def hari_kerja_list(self):
        """Return list of int hari kerja."""
        try:
            return [int(h) for h in self.hari_kerja.split(',') if h.strip()]
        except Exception:
            return [0, 1, 2, 3, 4]

    @property
    def durasi_jam(self):
        """Hitung durasi shift dalam jam (untuk fixed/split)."""
        if not self.jam_masuk or not self.jam_keluar:
            return float(self.minimal_jam_kerja)
        from datetime import datetime, date
        masuk  = datetime.combine(date.today(), self.jam_masuk)
        keluar = datetime.combine(date.today(), self.jam_keluar)
        if keluar <= masuk:  # overnight shift
            from datetime import timedelta
            keluar += timedelta(days=1)
        durasi = (keluar - masuk).seconds / 3600
        if self.tipe == 'split' and self.jam_masuk_2 and self.jam_keluar_2:
            masuk2  = datetime.combine(date.today(), self.jam_masuk_2)
            keluar2 = datetime.combine(date.today(), self.jam_keluar_2)
            durasi += (keluar2 - masuk2).seconds / 3600
        return round(durasi, 1)

    def hitung_keterlambatan(self, jam_check_in):
        """
        Hitung menit keterlambatan berdasarkan jam_masuk shift.
        Return 0 jika flexible atau masih dalam toleransi.
        """
        if self.tipe == 'flexible' or not self.jam_masuk or not jam_check_in:
            return 0
        from datetime import datetime, date
        masuk_standar = datetime.combine(date.today(), self.jam_masuk)
        masuk_aktual  = datetime.combine(date.today(), jam_check_in)
        delta_menit   = int((masuk_aktual - masuk_standar).total_seconds() / 60)
        return max(0, delta_menit - self.toleransi_telat)

    def hitung_lembur(self, jam_check_out):
        """
        Hitung jam lembur berdasarkan jam_keluar shift.
        Return 0 jika flexible.
        """
        if self.tipe == 'flexible' or not self.jam_keluar or not jam_check_out:
            return 0
        from datetime import datetime, date
        keluar_standar = datetime.combine(date.today(), self.jam_keluar)
        keluar_aktual  = datetime.combine(date.today(), jam_check_out)
        if keluar_aktual > keluar_standar:
            delta = (keluar_aktual - keluar_standar).total_seconds() / 3600
            return round(delta, 1)
        return 0


class ShiftAssignment(models.Model):
    """
    Assignment shift ke karyawan atau departemen.
    Support: per karyawan, per departemen, per hari-dalam-minggu.
    """
    HARI_CHOICES = [
        (0,'Senin'),(1,'Selasa'),(2,'Rabu'),(3,'Kamis'),
        (4,'Jumat'),(5,'Sabtu'),(6,'Minggu'),
    ]

    # Target: salah satu harus diisi
    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                   null=True, blank=True, related_name='shift_assignments',
                                   verbose_name='Karyawan')
    department = models.ForeignKey(Department, on_delete=models.CASCADE,
                                   null=True, blank=True, related_name='shift_assignments',
                                   verbose_name='Departemen')

    shift      = models.ForeignKey(Shift, on_delete=models.CASCADE,
                                   related_name='assignments', verbose_name='Shift')

    # Rentang berlaku
    berlaku_mulai  = models.DateField(verbose_name='Berlaku Mulai')
    berlaku_sampai = models.DateField(null=True, blank=True,
                                      verbose_name='Berlaku Sampai',
                                      help_text='Kosongkan = berlaku permanen')

    # Hari spesifik (untuk jadwal mingguan)
    # Kosong = berlaku semua hari kerja shift
    hari_spesifik = models.IntegerField(null=True, blank=True,
                                         choices=HARI_CHOICES,
                                         verbose_name='Hari Spesifik',
                                         help_text='Kosongkan = berlaku semua hari shift')

    keterangan = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Assignment Shift'
        verbose_name_plural = 'Assignment Shift'
        ordering = ['-berlaku_mulai']

    def __str__(self):
        target = self.employee.nama if self.employee else f"Dept: {self.department}"
        return f"{target} → {self.shift.kode} (mulai {self.berlaku_mulai})"

    def is_active_on(self, tgl):
        """Cek apakah assignment aktif pada tanggal tertentu."""
        if tgl < self.berlaku_mulai:
            return False
        if self.berlaku_sampai and tgl > self.berlaku_sampai:
            return False
        if self.hari_spesifik is not None and tgl.weekday() != self.hari_spesifik:
            return False
        return True


class ShiftRoster(models.Model):
    """
    Roster harian — shift yang dijadwalkan untuk karyawan pada tanggal tertentu.
    Ini yang dipakai untuk rotating & roster bulanan.
    Override ShiftAssignment jika ada.
    """
    employee  = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                  related_name='roster_entries', verbose_name='Karyawan')
    tanggal   = models.DateField(verbose_name='Tanggal')
    shift     = models.ForeignKey(Shift, on_delete=models.CASCADE,
                                  null=True, blank=True,
                                  verbose_name='Shift',
                                  help_text='Kosongkan = hari libur/off')
    is_off    = models.BooleanField(default=False, verbose_name='Hari Off/Libur')
    keterangan = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Roster'
        verbose_name_plural = 'Roster'
        unique_together = ['employee', 'tanggal']
        ordering = ['tanggal', 'employee__nama']

    def __str__(self):
        shift_str = self.shift.kode if self.shift else 'OFF'
        return f"{self.employee.nama} | {self.tanggal} | {shift_str}"


# ── Helper function (dipakai oleh attendance & payroll) ───────────────────────

def get_shift_for_employee(employee, tanggal):
    """
    Ambil shift yang berlaku untuk karyawan pada tanggal tertentu.
    Prioritas: Roster > ShiftAssignment karyawan > ShiftAssignment departemen
    Return: Shift object atau None.
    """
    # 1. Cek roster harian
    roster = ShiftRoster.objects.filter(employee=employee, tanggal=tanggal).first()
    if roster:
        return None if roster.is_off else roster.shift

    # 2. Cek assignment per karyawan
    assignments = ShiftAssignment.objects.filter(
        employee=employee,
        berlaku_mulai__lte=tanggal,
    ).filter(
        models.Q(berlaku_sampai__isnull=True) | models.Q(berlaku_sampai__gte=tanggal)
    ).select_related('shift').order_by('-berlaku_mulai')

    for a in assignments:
        if a.is_active_on(tanggal):
            return a.shift

    # 3. Cek assignment per departemen
    if employee.department:
        dept_assignments = ShiftAssignment.objects.filter(
            department=employee.department,
            employee__isnull=True,
            berlaku_mulai__lte=tanggal,
        ).filter(
            models.Q(berlaku_sampai__isnull=True) | models.Q(berlaku_sampai__gte=tanggal)
        ).select_related('shift').order_by('-berlaku_mulai')

        for a in dept_assignments:
            if a.is_active_on(tanggal):
                return a.shift

    return None
