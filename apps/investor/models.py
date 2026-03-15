"""
apps/investor/models.py
"""
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from decimal import Decimal


class InvestorPool(models.Model):
    """Konfigurasi pool — hanya founder yang bisa lihat lewat admin."""
    nama            = models.CharField(max_length=100, default='Pool Investasi Ikira')
    total_dana      = models.DecimalField(max_digits=12, decimal_places=0, default=4000000,
                                          verbose_name='Total Dana Pool (Rp)')
    modal_founder   = models.DecimalField(max_digits=12, decimal_places=0, default=2000000,
                                          verbose_name='Modal Founder (Rp)')
    persen_investor = models.DecimalField(max_digits=5, decimal_places=2, default=50,
                                          verbose_name='% Nett untuk Investor Pool (%)')
    target_return_x = models.DecimalField(max_digits=4, decimal_places=1, default=2,
                                          verbose_name='Target Return (x lipat)')
    aktif           = models.BooleanField(default=True)
    catatan         = models.TextField(blank=True, verbose_name='Catatan Internal Founder')

    class Meta:
        verbose_name        = 'Konfigurasi Pool Investasi'
        verbose_name_plural = 'Konfigurasi Pool Investasi'

    def __str__(self):
        return self.nama

    @property
    def total_investor_pool(self):
        return self.total_dana - self.modal_founder


class InvestorAccount(models.Model):
    pool            = models.ForeignKey(InvestorPool, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='investors')
    nama            = models.CharField(max_length=100)
    username        = models.CharField(max_length=50, unique=True)
    password        = models.CharField(max_length=255)
    aktif           = models.BooleanField(default=True)
    modal_investasi = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                          verbose_name='Modal Investasi (Rp)')
    total_diterima  = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                          verbose_name='Total Sudah Diterima (Rp)')
    tanggal_mulai   = models.DateField(null=True, blank=True)
    catatan_founder = models.TextField(blank=True, verbose_name='Catatan Founder (rahasia)')
    created_at      = models.DateTimeField(auto_now_add=True)
    last_login      = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Akun Investor'
        verbose_name_plural = 'Akun Investor'

    def __str__(self):
        return f'{self.nama} ({self.username})'

    def set_password(self, raw):
        self.password = make_password(raw)

    def check_password(self, raw):
        return check_password(raw, self.password)

    @property
    def total_investor_pool(self):
        if self.pool:
            return self.pool.total_investor_pool
        return Decimal('0')

    @property
    def porsi_persen(self):
        pool_total = self.total_investor_pool
        if not pool_total or pool_total == 0:
            return Decimal('0')
        return (self.modal_investasi / pool_total * 100).quantize(Decimal('0.01'))

    @property
    def target_total_return(self):
        multiplier = self.pool.target_return_x if self.pool else Decimal('2')
        return self.modal_investasi * multiplier

    @property
    def sisa_target(self):
        return max(self.target_total_return - self.total_diterima, Decimal('0'))

    @property
    def progress_persen(self):
        if not self.target_total_return or self.target_total_return == 0:
            return 0
        return min(float(self.total_diterima / self.target_total_return * 100), 100)

    @property
    def status_return(self):
        return 'lunas' if self.total_diterima >= self.target_total_return else 'berjalan'

    def estimasi_bulan_ini(self, nett_revenue):
        if not self.pool or self.total_investor_pool == 0:
            return Decimal('0')
        bagian_pool = nett_revenue * (self.pool.persen_investor / 100)
        return (bagian_pool * self.porsi_persen / 100).quantize(Decimal('1'))


class PayoutHistory(models.Model):
    investor    = models.ForeignKey(InvestorAccount, on_delete=models.CASCADE, related_name='payouts')
    bulan       = models.DateField()
    jumlah      = models.DecimalField(max_digits=12, decimal_places=0)
    keterangan  = models.CharField(max_length=200, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Riwayat Payout'
        verbose_name_plural = 'Riwayat Payout'
        ordering            = ['-bulan']
        unique_together     = ['investor', 'bulan']

    def __str__(self):
        return f'{self.investor.nama} — {self.bulan.strftime("%B %Y")} — Rp {self.jumlah:,.0f}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        total = PayoutHistory.objects.filter(investor=self.investor).aggregate(
            total=models.Sum('jumlah'))['total'] or 0
        self.investor.total_diterima = total
        self.investor.save(update_fields=['total_diterima'])


class Milestone(models.Model):
    STATUS_CHOICES = [
        ('done',    'Selesai'),
        ('ongoing', 'Sedang Berjalan'),
        ('planned', 'Direncanakan'),
    ]
    judul       = models.CharField(max_length=200)
    deskripsi   = models.TextField(blank=True)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='planned')
    target_date = models.DateField(null=True, blank=True)
    urutan      = models.IntegerField(default=0)

    class Meta:
        verbose_name        = 'Milestone'
        verbose_name_plural = 'Milestones'
        ordering            = ['urutan']

    def __str__(self):
        return f'[{self.get_status_display()}] {self.judul}'


class RevenueEntry(models.Model):
    bulan       = models.DateField()
    mrr         = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    biaya_ops   = models.DecimalField(max_digits=12, decimal_places=0, default=800000,
                                      verbose_name='Biaya Operasional (Rp)')
    client_baru = models.IntegerField(default=0)
    catatan     = models.TextField(blank=True)

    class Meta:
        verbose_name        = 'Revenue Entry'
        verbose_name_plural = 'Revenue Entries'
        ordering            = ['-bulan']
        unique_together     = ['bulan']

    def __str__(self):
        return f'{self.bulan.strftime("%B %Y")} — Rp {self.mrr:,.0f}'

    @property
    def nett(self):
        return max(self.mrr - self.biaya_ops, Decimal('0'))
