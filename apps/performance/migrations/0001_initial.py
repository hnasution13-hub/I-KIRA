from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PeriodePenilaian',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama', models.CharField(max_length=100, verbose_name='Nama Periode')),
                ('tipe', models.CharField(choices=[('Bulanan', 'Bulanan'), ('Triwulan', 'Triwulan (Q)'), ('Semesteran', 'Semesteran'), ('Tahunan', 'Tahunan')], default='Tahunan', max_length=15)),
                ('tanggal_mulai', models.DateField(verbose_name='Tanggal Mulai')),
                ('tanggal_selesai', models.DateField(verbose_name='Tanggal Selesai')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('aktif', 'Aktif'), ('tutup', 'Ditutup')], default='draft', max_length=10)),
                ('deskripsi', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='periode_penilaian', to='core.company')),
            ],
            options={'verbose_name': 'Periode Penilaian', 'verbose_name_plural': 'Periode Penilaian', 'ordering': ['-tanggal_mulai']},
        ),
        migrations.CreateModel(
            name='KPITemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama', models.CharField(max_length=200, verbose_name='Nama Indikator')),
                ('deskripsi', models.TextField(blank=True, verbose_name='Deskripsi')),
                ('satuan', models.CharField(choices=[('%', 'Persentase (%)'), ('angka', 'Angka'), ('rupiah', 'Rupiah (Rp)'), ('hari', 'Hari'), ('jam', 'Jam'), ('unit', 'Unit'), ('lainnya', 'Lainnya')], default='%', max_length=10)),
                ('arah', models.CharField(choices=[('tinggi', 'Semakin Tinggi Semakin Baik'), ('rendah', 'Semakin Rendah Semakin Baik')], default='tinggi', max_length=10, verbose_name='Arah Penilaian')),
                ('kategori', models.CharField(blank=True, help_text='Misal: Keuangan, Pelanggan, Proses, SDM', max_length=100, verbose_name='Kategori/Perspektif')),
                ('aktif', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kpi_templates', to='core.company')),
            ],
            options={'verbose_name': 'Template KPI', 'verbose_name_plural': 'Template KPI', 'ordering': ['kategori', 'nama']},
        ),
        migrations.CreateModel(
            name='PenilaianKaryawan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('submit', 'Diajukan'), ('review', 'Dalam Review Atasan'), ('approved', 'Disetujui'), ('rejected', 'Dikembalikan')], default='draft', max_length=10)),
                ('catatan_karyawan', models.TextField(blank=True, verbose_name='Catatan Karyawan')),
                ('catatan_atasan', models.TextField(blank=True, verbose_name='Catatan Atasan')),
                ('skor_kpi', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Skor KPI (%)')),
                ('skor_review', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Skor Review Atasan (%)')),
                ('skor_akhir', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Skor Akhir (%)')),
                ('predikat', models.CharField(blank=True, max_length=30, verbose_name='Predikat')),
                ('tanggal_submit', models.DateTimeField(blank=True, null=True)),
                ('tanggal_approve', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='penilaian', to='core.company')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='penilaian', to='employees.employee')),
                ('periode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='penilaian', to='performance.periodepenilaian')),
                ('atasan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='penilaian_sebagai_atasan', to='employees.employee', verbose_name='Penilai / Atasan')),
            ],
            options={'verbose_name': 'Penilaian Karyawan', 'verbose_name_plural': 'Penilaian Karyawan', 'ordering': ['-created_at'], 'unique_together': {('employee', 'periode')}},
        ),
        migrations.CreateModel(
            name='KPIItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama_kpi', models.CharField(max_length=200, verbose_name='Nama KPI')),
                ('satuan', models.CharField(default='%', max_length=10)),
                ('arah', models.CharField(default='tinggi', max_length=10)),
                ('bobot', models.DecimalField(decimal_places=2, default=20, max_digits=5, verbose_name='Bobot (%)')),
                ('target', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Target')),
                ('realisasi', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Realisasi')),
                ('catatan', models.TextField(blank=True)),
                ('penilaian', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kpi_items', to='performance.PenilaianKaryawan')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='kpi_items', to='performance.kpitemplate')),
            ],
            options={'verbose_name': 'KPI Item', 'verbose_name_plural': 'KPI Items', 'ordering': ['nama_kpi']},
        ),
        migrations.CreateModel(
            name='ReviewAtasan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aspek', models.CharField(help_text='Misal: Kedisiplinan, Komunikasi, Teamwork', max_length=100, verbose_name='Aspek Penilaian')),
                ('bobot', models.DecimalField(decimal_places=2, default=20, max_digits=5, verbose_name='Bobot (%)')),
                ('skor', models.IntegerField(blank=True, choices=[(1, '1 — Sangat Kurang'), (2, '2 — Kurang'), (3, '3 — Cukup'), (4, '4 — Baik'), (5, '5 — Sangat Baik')], null=True)),
                ('catatan', models.TextField(blank=True)),
                ('penilaian', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_items', to='performance.PenilaianKaryawan')),
            ],
            options={'verbose_name': 'Review Atasan', 'verbose_name_plural': 'Review Atasan'},
        ),
    ]
