from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0001_initial'),
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SitePayrollSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_label', models.CharField(default='Kantor Pusat / Tidak Ada Site', max_length=100, verbose_name='Label Site')),
                ('jumlah_karyawan', models.IntegerField(default=0)),
                ('total_gaji_kotor', models.BigIntegerField(default=0)),
                ('total_tunjangan', models.BigIntegerField(default=0)),
                ('total_potongan', models.BigIntegerField(default=0)),
                ('total_gaji_bersih', models.BigIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='site_summaries', to='payroll.payroll')),
                ('job_site', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payroll_summaries', to='employees.jobsite', verbose_name='Job Site')),
            ],
            options={
                'verbose_name': 'Site Payroll Summary',
                'verbose_name_plural': 'Site Payroll Summaries',
                'ordering': ['site_label'],
                'unique_together': {('payroll', 'job_site')},
            },
        ),
    ]
