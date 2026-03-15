from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0002_sitepayrollsummary'),
        ('core', '0001_initial'),
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteAllowanceRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama_komponen', models.CharField(default='Tunjangan Site', max_length=100, verbose_name='Nama Komponen')),
                ('nilai', models.BigIntegerField(default=0, verbose_name='Nilai (Rp atau %)')),
                ('jenis', models.CharField(
                    choices=[('flat', 'Nominal Tetap (Rp)'), ('persen', 'Persentase Gaji Pokok (%)')],
                    default='flat', max_length=10, verbose_name='Jenis')),
                ('aktif', models.BooleanField(default=True, verbose_name='Aktif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='site_allowance_rules', to='core.company')),
                ('jabatan', models.ForeignKey(
                    blank=True, null=True,
                    help_text='Kosongkan = berlaku untuk semua jabatan di site ini',
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='site_allowance_rules', to='core.position',
                    verbose_name='Jabatan (opsional)')),
                ('job_site', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='allowance_rules', to='employees.jobsite',
                    verbose_name='Job Site')),
            ],
            options={
                'verbose_name': 'Site Allowance Rule',
                'verbose_name_plural': 'Site Allowance Rules',
                'ordering': ['job_site', 'jabatan'],
            },
        ),
    ]
