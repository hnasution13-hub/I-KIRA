"""
TAMBAHKAN ke apps/shifts/models.py (append di bagian bawah)
=============================================================
Model ShiftCycle: pola berulang per karyawan.
Cocok untuk security dengan pola 4-3, 3-shift rotasi, 12 jam, dll.
"""
from django.db import models
from datetime import date, timedelta
import json


class ShiftCycle(models.Model):
    """
    Pola shift berulang (cyclic) per karyawan.

    Contoh pola security 4 kerja 3 off (3 shift):
      slot 0: PAGI-S  (hari 1)
      slot 1: PAGI-S  (hari 2)
      slot 2: SORE-S  (hari 3)
      slot 3: SORE-S  (hari 4)
      slot 4: None    (hari 5 - OFF)
      slot 5: None    (hari 6 - OFF)
      slot 6: None    (hari 7 - OFF)
      → ulang dari slot 0

    Pola disimpan sebagai JSON array shift_id atau null:
      "[1, 1, 2, 2, null, null, null]"
    """
    nama        = models.CharField(max_length=100, verbose_name='Nama Pola',
                                   help_text='cth: Security 4-3 Pagi, Security 12Jam Rotasi')
    keterangan  = models.TextField(blank=True)
    pola_json   = models.TextField(
        verbose_name='Pola Shift (JSON)',
        help_text='Array shift_id atau null. cth: [1,1,2,2,null,null,null]'
    )
    aktif       = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pola Shift Cyclic'
        verbose_name_plural = 'Pola Shift Cyclic'
        ordering = ['nama']

    def __str__(self):
        return f"{self.nama} ({self.panjang_siklus} hari/siklus)"

    @property
    def pola(self):
        """Return list of shift_id (int) or None."""
        try:
            return json.loads(self.pola_json)
        except Exception:
            return []

    @property
    def panjang_siklus(self):
        return len(self.pola)

    def get_shift_on_day(self, hari_ke):
        """
        Ambil shift_id untuk hari ke-N dalam siklus (0-based).
        Return None jika OFF.
        """
        p = self.pola
        if not p:
            return None
        return p[hari_ke % len(p)]

    def get_shift_for_date(self, tanggal, mulai_dari):
        """
        Ambil shift_id untuk tanggal tertentu berdasarkan mulai_dari.
        """
        delta = (tanggal - mulai_dari).days
        if delta < 0:
            return None
        return self.get_shift_on_day(delta)


class EmployeeShiftCycle(models.Model):
    """
    Assignment pola cyclic ke karyawan.
    Setiap karyawan bisa punya tanggal mulai berbeda
    → inilah yang membuat jadwal tiap personel unik.
    """
    employee    = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE,
        related_name='shift_cycles', verbose_name='Karyawan'
    )
    cycle       = models.ForeignKey(
        ShiftCycle, on_delete=models.CASCADE,
        related_name='assignments', verbose_name='Pola Shift'
    )
    mulai_dari  = models.DateField(verbose_name='Mulai Dari Tanggal',
                                   help_text='Hari pertama siklus dimulai untuk karyawan ini')
    berlaku_sampai = models.DateField(null=True, blank=True,
                                      verbose_name='Berlaku Sampai',
                                      help_text='Kosongkan = permanen')
    keterangan  = models.CharField(max_length=200, blank=True)
    aktif       = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Assignment Pola Cyclic'
        verbose_name_plural = 'Assignment Pola Cyclic'
        ordering = ['-mulai_dari']

    def __str__(self):
        return f"{self.employee.nama} → {self.cycle.nama} (mulai {self.mulai_dari})"

    def is_active_on(self, tgl):
        if tgl < self.mulai_dari:
            return False
        if self.berlaku_sampai and tgl > self.berlaku_sampai:
            return False
        return self.aktif

    def get_shift_id_for_date(self, tgl):
        """Return shift_id atau None (OFF) untuk tanggal ini."""
        if not self.is_active_on(tgl):
            return None
        return self.cycle.get_shift_for_date(tgl, self.mulai_dari)


# ── Helper: get shift dari cycle (dipakai attendance & payroll) ───────────────

def get_cycle_shift_for_employee(employee, tanggal):
    """
    Cek apakah karyawan punya pola cyclic aktif pada tanggal ini.
    Return Shift object atau None.
    Prioritas lebih rendah dari ShiftRoster, lebih tinggi dari ShiftAssignment biasa.
    """
    from apps.shifts.models import Shift

    assignment = EmployeeShiftCycle.objects.filter(
        employee=employee,
        aktif=True,
        mulai_dari__lte=tanggal,
    ).filter(
        models.Q(berlaku_sampai__isnull=True) | models.Q(berlaku_sampai__gte=tanggal)
    ).select_related('cycle').order_by('-mulai_dari').first()

    if not assignment:
        return None

    shift_id = assignment.get_shift_id_for_date(tanggal)
    if shift_id is None:
        return None  # Hari OFF dalam siklus
    if shift_id == 'OFF':
        return None

    try:
        return Shift.objects.get(pk=shift_id)
    except Shift.DoesNotExist:
        return None


def generate_roster_from_cycle(employee, year, month):
    """
    Auto-generate ShiftRoster untuk 1 bulan dari pola cyclic.
    Jika sudah ada roster manual untuk tanggal itu, skip (tidak override).
    Return: jumlah hari yang di-generate.
    """
    import calendar as cal_mod
    from apps.shifts.models import ShiftRoster

    _, days = cal_mod.monthrange(year, month)
    generated = 0

    for d in range(1, days + 1):
        tgl = date(year, month, d)

        # Skip jika sudah ada roster manual
        if ShiftRoster.objects.filter(employee=employee, tanggal=tgl).exists():
            continue

        shift = get_cycle_shift_for_employee(employee, tgl)

        # Cek apakah hari ini OFF dalam siklus (bukan tidak ada assignment)
        assignment = EmployeeShiftCycle.objects.filter(
            employee=employee, aktif=True,
            mulai_dari__lte=tgl,
        ).filter(
            models.Q(berlaku_sampai__isnull=True) | models.Q(berlaku_sampai__gte=tgl)
        ).order_by('-mulai_dari').first()

        if assignment:
            shift_id_raw = assignment.get_shift_id_for_date(tgl)
            is_off = (shift_id_raw is None)
            ShiftRoster.objects.create(
                employee=employee,
                tanggal=tgl,
                shift=shift,
                is_off=is_off,
                keterangan='Auto-generate dari pola cyclic'
            )
            generated += 1

    return generated
