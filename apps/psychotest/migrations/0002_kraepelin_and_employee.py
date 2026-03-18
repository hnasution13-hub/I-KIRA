import apps.psychotest.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('psychotest', '0001_initial'),
        ('employees', '0001_initial'),
        ('recruitment', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        # ── PsikotesSession — tambah employee, tujuan, durasi_kraepelin ──────
        migrations.AddField(
            model_name='psikotessession',
            name='employee',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='psychotest_sessions',
                to='employees.employee',
                verbose_name='Karyawan',
            ),
        ),
        migrations.AddField(
            model_name='psikotessession',
            name='tujuan',
            field=models.CharField(
                blank=True,
                choices=[
                    ('rekrutmen', 'Rekrutmen'),
                    ('berkala',   'Evaluasi Berkala'),
                    ('promosi',   'Promosi Jabatan'),
                    ('evaluasi',  'Evaluasi Kinerja'),
                ],
                default='rekrutmen',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='psikotessession',
            name='durasi_kraepelin',
            field=models.IntegerField(default=30),
        ),
        # PsikotesSession.candidate — ubah jadi nullable
        migrations.AlterField(
            model_name='psikotessession',
            name='candidate',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='psychotest_sessions',
                to='recruitment.candidate',
            ),
        ),
        # SoalBank — tambah kraepelin ke choices
        migrations.AlterField(
            model_name='soalbank',
            name='kategori',
            field=models.CharField(
                choices=[
                    ('logika',    'Logika'),
                    ('verbal',    'Verbal'),
                    ('numerik',   'Numerik'),
                    ('disc',      'DISC Personality'),
                    ('kraepelin', 'Kraepelin'),
                ],
                max_length=20,
            ),
        ),
        # PsikotesResult — tambah employee FK
        migrations.AddField(
            model_name='psikotesresult',
            name='employee',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='psychotest_results',
                to='employees.employee',
            ),
        ),
        migrations.AlterField(
            model_name='psikotesresult',
            name='candidate',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='psychotest_result_set',
                to='recruitment.candidate',
            ),
        ),

        # ── KraepelinSession ─────────────────────────────────────────────────
        migrations.CreateModel(
            name='KraepelinSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tujuan', models.CharField(
                    choices=[
                        ('rekrutmen', 'Rekrutmen'),
                        ('berkala',   'Evaluasi Berkala'),
                        ('promosi',   'Promosi Jabatan'),
                        ('evaluasi',  'Evaluasi Kinerja'),
                    ],
                    default='rekrutmen', max_length=20,
                )),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending',   'Belum Dikerjakan'),
                        ('started',   'Sedang Dikerjakan'),
                        ('completed', 'Selesai'),
                        ('expired',   'Kadaluarsa'),
                    ],
                    default='pending', max_length=20,
                )),
                ('jumlah_baris',    models.IntegerField(default=50)),
                ('digit_per_baris', models.IntegerField(default=60)),
                ('detik_per_baris', models.IntegerField(default=30)),
                ('seed',            models.IntegerField(default=0)),
                ('expired_at',      models.DateTimeField(default=apps.psychotest.models.default_expired)),
                ('started_at',      models.DateTimeField(blank=True, null=True)),
                ('completed_at',    models.DateTimeField(blank=True, null=True)),
                ('created_by',      models.CharField(blank=True, max_length=100)),
                ('created_at',      models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='kraepelin_sessions',
                    to='core.company',
                )),
                ('candidate', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='kraepelin_sessions',
                    to='recruitment.candidate',
                )),
                ('employee', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='kraepelin_sessions',
                    to='employees.employee',
                )),
            ],
            options={
                'verbose_name': 'Sesi Kraepelin',
                'verbose_name_plural': 'Sesi Kraepelin',
                'ordering': ['-created_at'],
            },
        ),

        # ── KraepelinRowResult ───────────────────────────────────────────────
        migrations.CreateModel(
            name='KraepelinRowResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('baris',        models.IntegerField(verbose_name='Nomor Baris (1-based)')),
                ('jawaban',      models.TextField(blank=True)),
                ('kunci',        models.TextField(blank=True)),
                ('dikerjakan',   models.IntegerField(default=0)),
                ('benar',        models.IntegerField(default=0)),
                ('salah',        models.IntegerField(default=0)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='row_results',
                    to='psychotest.kraepelinsession',
                )),
            ],
            options={
                'verbose_name': 'Hasil Baris Kraepelin',
                'ordering': ['baris'],
                'unique_together': {('session', 'baris')},
            },
        ),

        # ── KraepelinResult ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='KraepelinResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('skor_kecepatan',   models.FloatField(default=0)),
                ('skor_ketelitian',  models.FloatField(default=0)),
                ('skor_konsistensi', models.FloatField(default=0)),
                ('skor_ketahanan',   models.FloatField(default=0)),
                ('skor_total',       models.IntegerField(default=0)),
                ('grade',            models.CharField(blank=True, max_length=2)),
                ('detail',           models.JSONField(default=dict)),
                ('catatan_hr',       models.TextField(blank=True)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
                ('session', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='result',
                    to='psychotest.kraepelinsession',
                )),
                ('candidate', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='kraepelin_results',
                    to='recruitment.candidate',
                )),
                ('employee', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='kraepelin_results',
                    to='employees.employee',
                )),
            ],
            options={
                'verbose_name': 'Hasil Kraepelin',
                'verbose_name_plural': 'Hasil Kraepelin',
            },
        ),
    ]
