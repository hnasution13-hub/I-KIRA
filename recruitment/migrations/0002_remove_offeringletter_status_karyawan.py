# Generated manually to remove orphan column status_karyawan
# that exists in DB but not in the model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE recruitment_offeringletter DROP COLUMN IF EXISTS status_karyawan;",
            reverse_sql="ALTER TABLE recruitment_offeringletter ADD COLUMN status_karyawan VARCHAR(10) DEFAULT 'PKWT';",
        ),
    ]
