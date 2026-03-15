from django.utils import timezone
from .models import Movement

def generate_movement_document_no(movement_type):
    now = timezone.now()
    bulan = now.strftime("%m")
    tahun = now.strftime("%y")
    prefix = {
        'PENUGASAN': 'BA',
        'PENGEMBALIAN': 'BK',
        'SERVICE': 'SRV',
        'MUTASI': 'MT',
        'HILANG': 'HL',
        'DIJUAL': 'DJ'
    }.get(movement_type, 'DOC')
    count = Movement.objects.filter(
        movement_type=movement_type,
        movement_date__month=now.month,
        movement_date__year=now.year
    ).count() + 1
    return f"{prefix}-{bulan}{tahun}-{count:03d}"