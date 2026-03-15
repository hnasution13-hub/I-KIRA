from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkloadStandard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama_aktivitas', models.CharField(max_length=200, verbose_name='Nama Aktivitas / Beban Kerja')),
                ('standar_output', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Standar Output')),
                ('satuan', models.CharField(choices=[('jam/hari', 'Jam per Hari'), ('jam/minggu', 'Jam per Minggu'), ('unit/hari', 'Unit per Hari'), ('unit/bulan', 'Unit per Bulan')], default='jam/hari', max_length=15)),
                ('deskripsi', models.TextField(blank=True)),
                ('aktif', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workload_standards', to='core.company')),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workload_standards', to='core.department')),
                ('jabatan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workload_standards', to='core.position', verbose_name='Jabatan')),
            ],
            options={
                'verbose_name': 'Workload Standard',
                'verbose_name_plural': 'Workload Standards',
                'ordering': ['department', 'jabatan', 'nama_aktivitas'],
            },
        ),
        migrations.CreateModel(
            name='FTEStandard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fte_ideal', models.DecimalField(decimal_places=2, help_text='Jumlah headcount ideal untuk posisi ini', max_digits=6, verbose_name='FTE Ideal')),
                ('fte_minimum', models.DecimalField(decimal_places=2, default=1, max_digits=6, verbose_name='FTE Minimum')),
                ('dasar_perhitungan', models.TextField(blank=True, help_text='Asumsi / metode yang digunakan', verbose_name='Dasar Perhitungan')),
                ('tahun', models.IntegerField(verbose_name='Tahun Referensi')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fte_standards', to='core.company')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fte_standards', to='core.department')),
                ('jabatan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fte_standards', to='core.position')),
            ],
            options={
                'verbose_name': 'FTE Standard',
                'verbose_name_plural': 'FTE Standards',
                'ordering': ['department', 'jabatan'],
                'unique_together': {('company', 'department', 'jabatan', 'tahun')},
            },
        ),
        migrations.CreateModel(
            name='FTEPlanningResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tanggal_analisis', models.DateField(auto_now_add=True, verbose_name='Tanggal Analisis')),
                ('headcount_aktual', models.IntegerField(verbose_name='Headcount Aktual')),
                ('fte_ideal', models.DecimalField(decimal_places=2, max_digits=6)),
                ('gap', models.DecimalField(decimal_places=2, max_digits=6, verbose_name='Gap (Aktual - Ideal)')),
                ('status', models.CharField(choices=[('over', 'Over-staffed'), ('ideal', 'Ideal'), ('under', 'Under-staffed')], max_length=10)),
                ('catatan', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fte_results', to='core.company')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fte_results', to='core.department')),
                ('jabatan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fte_results', to='core.position')),
                ('fte_standard', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='od.ftestandard')),
            ],
            options={
                'verbose_name': 'FTE Planning Result',
                'verbose_name_plural': 'FTE Planning Results',
                'ordering': ['-tanggal_analisis', 'department'],
            },
        ),
    ]
