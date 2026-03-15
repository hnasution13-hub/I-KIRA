import os
import uuid
from django.utils import timezone

def generate_asset_tag(prefix='AST'):
    date_str = timezone.now().strftime('%Y%m%d')
    unique_id = uuid.uuid4().hex[:4].upper()
    return f"{prefix}-{date_str}-{unique_id}"

def asset_photo_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.asset_code}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('assets', 'photos', filename)