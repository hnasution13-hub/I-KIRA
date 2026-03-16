from django.db import models


class Provinsi(models.Model):
    kode = models.CharField(max_length=20, unique=True, verbose_name='Kode')
    nama = models.CharField(max_length=100, verbose_name='Nama Provinsi')

    class Meta:
        verbose_name = 'Provinsi'
        verbose_name_plural = 'Provinsi'
        ordering = ['nama']

    def __str__(self):
        return self.nama


class Kabupaten(models.Model):
    provinsi = models.ForeignKey(Provinsi, on_delete=models.CASCADE, related_name='kabupatens')
    kode = models.CharField(max_length=20, unique=True, verbose_name='Kode')
    nama = models.CharField(max_length=100, verbose_name='Nama Kabupaten/Kota')

    class Meta:
        verbose_name = 'Kabupaten/Kota'
        verbose_name_plural = 'Kabupaten/Kota'
        ordering = ['nama']

    def __str__(self):
        return self.nama


class Kecamatan(models.Model):
    kabupaten = models.ForeignKey(Kabupaten, on_delete=models.CASCADE, related_name='kecamatans')
    kode = models.CharField(max_length=20, unique=True, verbose_name='Kode')
    nama = models.CharField(max_length=100, verbose_name='Nama Kecamatan')

    class Meta:
        verbose_name = 'Kecamatan'
        verbose_name_plural = 'Kecamatan'
        ordering = ['nama']

    def __str__(self):
        return self.nama


class Kelurahan(models.Model):
    kecamatan = models.ForeignKey(Kecamatan, on_delete=models.CASCADE, related_name='kelurahans')
    kode = models.CharField(max_length=20, unique=True, verbose_name='Kode')
    nama = models.CharField(max_length=100, verbose_name='Nama Kelurahan/Desa')
    kode_pos = models.CharField(max_length=10, blank=True, verbose_name='Kode Pos')

    class Meta:
        verbose_name = 'Kelurahan/Desa'
        verbose_name_plural = 'Kelurahan/Desa'
        ordering = ['nama']

    def __str__(self):
        return self.nama


class Bank(models.Model):
    kode  = models.CharField(max_length=20, unique=True, verbose_name='Kode Bank')
    nama  = models.CharField(max_length=200, verbose_name='Nama Bank')
    alias = models.CharField(max_length=50, blank=True, verbose_name='Alias / Singkatan',
                             help_text='Contoh: BRI, BCA, Mandiri. Diisi otomatis dari CSV.')

    class Meta:
        verbose_name        = 'Bank'
        verbose_name_plural = 'Bank'
        ordering            = ['nama']

    def __str__(self):
        return self.nama

    @property
    def nama_singkat(self):
        """Ambil nama pendek bank untuk dropdown: BCA, BRI, Mandiri, dll."""
        nama = self.nama.upper()
        shortcuts = {
            'RAKYAT INDONESIA': 'BRI', 'MANDIRI': 'Mandiri',
            'NEGARA INDONESIA': 'BNI', 'CENTRAL ASIA': 'BCA',
            'DANAMON': 'Danamon', 'CIMB NIAGA': 'CIMB Niaga',
            'PERMATA': 'Permata', 'OCBC': 'OCBC NISP',
            'MAYBANK': 'Maybank', 'PANIN': 'Panin',
            'BUKOPIN': 'Bukopin', 'BTN': 'BTN',
        }
        for key, short in shortcuts.items():
            if key in nama:
                return short
        # Fallback: ambil kata setelah PT./BANK
        import re
        match = re.search(r'BANK\s+(\w+)', nama)
        return match.group(1).title() if match else self.nama