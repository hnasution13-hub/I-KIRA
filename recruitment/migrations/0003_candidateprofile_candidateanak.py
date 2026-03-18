from django.db import migrations, models
import django.db.models.deletion
import uuid
import apps.recruitment.models_profile


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0002_offeringletter_status_karyawan_jangka_waktu'),
        ('wilayah', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CandidateProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('candidate', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to='recruitment.candidate',
                    verbose_name='Kandidat',
                )),
                ('token', models.UUIDField(default=uuid.uuid4, unique=True, editable=False)),
                ('token_created_at', models.DateTimeField(auto_now_add=True)),
                ('token_expires_at', models.DateTimeField(
                    default=apps.recruitment.models_profile.default_token_expires)),
                ('is_submitted', models.BooleanField(default=False, verbose_name='Sudah Diisi')),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('is_reviewed', models.BooleanField(default=False, verbose_name='Sudah Di-review HR')),
                ('reviewed_by', models.CharField(blank=True, max_length=100)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                # Data Pribadi
                ('tempat_lahir', models.CharField(blank=True, max_length=100, verbose_name='Tempat Lahir')),
                ('tanggal_lahir', models.DateField(blank=True, null=True, verbose_name='Tanggal Lahir')),
                ('jenis_kelamin', models.CharField(
                    blank=True, max_length=1,
                    choices=[('L', 'Laki-laki'), ('P', 'Perempuan')],
                    verbose_name='Jenis Kelamin')),
                ('agama', models.CharField(
                    blank=True, max_length=20,
                    choices=[('Islam','Islam'),('Kristen','Kristen'),('Katolik','Katolik'),
                             ('Hindu','Hindu'),('Buddha','Buddha'),('Konghucu','Konghucu')],
                    verbose_name='Agama')),
                ('pendidikan', models.CharField(
                    blank=True, max_length=10,
                    choices=[('SD','SD'),('SMP','SMP'),('SMA/SMK','SMA/SMK'),
                             ('D1','D1'),('D2','D2'),('D3','D3'),
                             ('D4/S1','D4/S1'),('S2','S2'),('S3','S3')],
                    verbose_name='Pendidikan Terakhir')),
                ('golongan_darah', models.CharField(
                    blank=True, max_length=4,
                    choices=[('A','A'),('B','B'),('AB','AB'),('O','O'),
                             ('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
                             ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-')],
                    verbose_name='Golongan Darah')),
                ('status_nikah', models.CharField(
                    blank=True, max_length=10,
                    choices=[('Lajang','Lajang'),('Menikah','Menikah'),('Cerai','Cerai')],
                    verbose_name='Status Pernikahan')),
                ('jumlah_anak', models.PositiveSmallIntegerField(default=0, verbose_name='Jumlah Anak')),
                ('ptkp', models.CharField(
                    blank=True, max_length=10,
                    choices=[('TK/0','TK/0'),('TK/1','TK/1'),('TK/2','TK/2'),('TK/3','TK/3'),
                             ('K/0','K/0'),('K/1','K/1'),('K/2','K/2'),('K/3','K/3'),
                             ('K/I/0','K/I/0'),('K/I/1','K/I/1'),('K/I/2','K/I/2'),('K/I/3','K/I/3')],
                    verbose_name='PTKP')),
                # Dokumen
                ('no_ktp', models.CharField(blank=True, max_length=20, verbose_name='No. KTP')),
                ('no_kk', models.CharField(blank=True, max_length=20, verbose_name='No. KK')),
                ('no_npwp', models.CharField(blank=True, max_length=25, verbose_name='No. NPWP')),
                ('no_bpjs_kes', models.CharField(blank=True, max_length=30, verbose_name='No. BPJS Kesehatan')),
                ('no_bpjs_tk', models.CharField(blank=True, max_length=30, verbose_name='No. BPJS Ketenagakerjaan')),
                # Rekening
                ('no_rek', models.CharField(blank=True, max_length=30, verbose_name='No. Rekening')),
                ('nama_bank', models.CharField(blank=True, max_length=200, verbose_name='Nama Bank')),
                ('nama_rek', models.CharField(blank=True, max_length=100, verbose_name='Nama di Rekening')),
                # Alamat
                ('alamat', models.TextField(blank=True, verbose_name='Alamat Lengkap')),
                ('rt', models.CharField(blank=True, max_length=5, verbose_name='RT')),
                ('rw', models.CharField(blank=True, max_length=5, verbose_name='RW')),
                ('kode_pos', models.CharField(blank=True, max_length=10, verbose_name='Kode Pos')),
                ('provinsi', models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='wilayah.provinsi', verbose_name='Provinsi')),
                ('kabupaten', models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='wilayah.kabupaten', verbose_name='Kabupaten/Kota')),
                ('kecamatan', models.CharField(blank=True, max_length=100, verbose_name='Kecamatan')),
                ('kelurahan', models.CharField(blank=True, max_length=100, verbose_name='Kelurahan/Desa')),
                # Kontak Darurat
                ('nama_darurat', models.CharField(blank=True, max_length=100, verbose_name='Nama Kontak Darurat')),
                ('hub_darurat', models.CharField(blank=True, max_length=50, verbose_name='Hubungan')),
                ('hp_darurat', models.CharField(blank=True, max_length=20, verbose_name='No. HP Darurat')),
                # Upload
                ('foto', models.ImageField(blank=True, null=True,
                    upload_to=apps.recruitment.models_profile._doc_upload('foto'),
                    verbose_name='Foto')),
                ('scan_ktp', models.FileField(blank=True, null=True,
                    upload_to=apps.recruitment.models_profile._doc_upload('ktp'),
                    verbose_name='Scan KTP')),
                ('scan_ijazah', models.FileField(blank=True, null=True,
                    upload_to=apps.recruitment.models_profile._doc_upload('ijazah'),
                    verbose_name='Scan Ijazah')),
                ('scan_skck', models.FileField(blank=True, null=True,
                    upload_to=apps.recruitment.models_profile._doc_upload('skck'),
                    verbose_name='Scan SKCK')),
                ('scan_npwp', models.FileField(blank=True, null=True,
                    upload_to=apps.recruitment.models_profile._doc_upload('npwp'),
                    verbose_name='Scan NPWP')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Profil Kandidat',
                'verbose_name_plural': 'Profil Kandidat',
            },
        ),
        migrations.CreateModel(
            name='CandidateAnak',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('profile', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='anak_list',
                    to='recruitment.candidateprofile',
                    verbose_name='Profil',
                )),
                ('urutan', models.PositiveSmallIntegerField(verbose_name='Urutan')),
                ('nama', models.CharField(max_length=200, verbose_name='Nama Anak')),
                ('tgl_lahir', models.DateField(blank=True, null=True, verbose_name='Tgl Lahir')),
                ('jenis_kelamin', models.CharField(
                    blank=True, max_length=1,
                    choices=[('L', 'Laki-laki'), ('P', 'Perempuan')])),
                ('no_bpjs_kes', models.CharField(blank=True, max_length=30,
                                                  verbose_name='No. BPJS Kes')),
            ],
            options={
                'verbose_name': 'Data Anak Kandidat',
                'ordering': ['urutan'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='candidateanak',
            unique_together={('profile', 'urutan')},
        ),
    ]
