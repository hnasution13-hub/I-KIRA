from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('od', '0001_initial'),
        ('core', '0001_initial'),
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompetencyCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama', models.CharField(max_length=100, verbose_name='Nama Kategori')),
                ('deskripsi', models.TextField(blank=True)),
                ('warna', models.CharField(default='#818cf8', max_length=7, verbose_name='Warna (hex)')),
                ('urutan', models.IntegerField(default=0)),
                ('aktif', models.BooleanField(default=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competency_categories', to='core.company')),
            ],
            options={'verbose_name': 'Competency Category', 'verbose_name_plural': 'Competency Categories', 'ordering': ['urutan', 'nama']},
        ),
        migrations.CreateModel(
            name='Competency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kode', models.CharField(max_length=20, verbose_name='Kode')),
                ('nama', models.CharField(max_length=150, verbose_name='Nama Kompetensi')),
                ('deskripsi', models.TextField(blank=True)),
                ('level_1_desc', models.TextField(blank=True, verbose_name='Deskripsi Level 1 (Dasar)')),
                ('level_2_desc', models.TextField(blank=True, verbose_name='Deskripsi Level 2 (Berkembang)')),
                ('level_3_desc', models.TextField(blank=True, verbose_name='Deskripsi Level 3 (Kompeten)')),
                ('level_4_desc', models.TextField(blank=True, verbose_name='Deskripsi Level 4 (Mahir)')),
                ('level_5_desc', models.TextField(blank=True, verbose_name='Deskripsi Level 5 (Ahli/Expert)')),
                ('aktif', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competencies', to='core.company')),
                ('kategori', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='competencies', to='od.competencycategory')),
            ],
            options={'verbose_name': 'Kompetensi', 'verbose_name_plural': 'Kompetensi', 'ordering': ['kategori', 'kode'], 'unique_together': {('company', 'kode')}},
        ),
        migrations.CreateModel(
            name='PositionCompetency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level_required', models.IntegerField(choices=[(1, 'Level 1'), (2, 'Level 2'), (3, 'Level 3'), (4, 'Level 4'), (5, 'Level 5')], default=3, verbose_name='Level yang Dibutuhkan')),
                ('bobot', models.IntegerField(default=1, help_text='Kepentingan kompetensi ini untuk jabatan', verbose_name='Bobot (1-5)')),
                ('wajib', models.BooleanField(default=True, verbose_name='Wajib / Mandatory')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='position_competencies', to='core.company')),
                ('competency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='position_requirements', to='od.competency')),
                ('jabatan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='required_competencies', to='core.position')),
            ],
            options={'verbose_name': 'Standar Kompetensi Jabatan', 'verbose_name_plural': 'Standar Kompetensi Jabatan', 'ordering': ['-wajib', '-bobot'], 'unique_together': {('jabatan', 'competency')}},
        ),
        migrations.CreateModel(
            name='EmployeeCompetency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level_aktual', models.IntegerField(choices=[(1, 'Level 1'), (2, 'Level 2'), (3, 'Level 3'), (4, 'Level 4'), (5, 'Level 5')], default=1, verbose_name='Level Aktual')),
                ('metode', models.CharField(choices=[('self', 'Self Assessment'), ('manager', 'Manager Assessment'), ('360', '360° Assessment'), ('test', 'Uji Kompetensi')], default='manager', max_length=10)),
                ('catatan', models.TextField(blank=True)),
                ('tanggal_penilaian', models.DateField(auto_now_add=True, verbose_name='Tanggal Penilaian')),
                ('periode', models.CharField(help_text='Contoh: 2026', max_length=7, verbose_name='Periode (YYYY)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_competencies', to='core.company')),
                ('competency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_assessments', to='od.competency')),
                ('dinilai_oleh', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='competency_assessor', to='employees.employee', verbose_name='Dinilai Oleh')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competency_assessments', to='employees.employee')),
            ],
            options={'verbose_name': 'Penilaian Kompetensi Karyawan', 'verbose_name_plural': 'Penilaian Kompetensi Karyawan', 'ordering': ['-tanggal_penilaian'], 'unique_together': {('employee', 'competency', 'periode')}},
        ),
    ]
