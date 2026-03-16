from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='offeringletter',
            name='status_karyawan',
            field=models.CharField(
                choices=[('PKWT', 'PKWT (Kontrak)'), ('PKWTT', 'PKWTT (Permanen)'), ('PHL', 'PHL (Harian Lepas)')],
                default='PKWT',
                max_length=10,
                verbose_name='Status Karyawan',
            ),
        ),
        migrations.AddField(
            model_name='offeringletter',
            name='jangka_waktu',
            field=models.CharField(
                blank=True,
                default='',
                max_length=100,
                verbose_name='Jangka Waktu Perjanjian',
            ),
        ),
    ]
