# hris_project/supabase_storage.py
"""
Custom Django storage backend menggunakan Supabase Storage.
File media (CV, foto, dll) disimpan ke Supabase Storage bucket,
bukan ke disk lokal — aman di Render free tier (ephemeral filesystem).
"""

import os
import mimetypes
from urllib.parse import urljoin

from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.conf import settings


@deconstructible
class SupabaseStorage(Storage):
    """
    Django Storage backend untuk Supabase Storage.
    Semua file media disimpan ke bucket Supabase.
    """

    def __init__(self, bucket=None, supabase_url=None, service_key=None):
        self.bucket      = bucket      or getattr(settings, 'SUPABASE_BUCKET', 'ikira-media')
        self.supabase_url = supabase_url or getattr(settings, 'SUPABASE_URL', '')
        self.service_key  = service_key  or getattr(settings, 'SUPABASE_SERVICE_KEY', '')

    def _get_client(self):
        """Buat HTTP session untuk Supabase Storage API."""
        import urllib.request
        return {
            'url':  f'{self.supabase_url}/storage/v1/object',
            'headers': {
                'Authorization': f'Bearer {self.service_key}',
                'apikey': self.service_key,
            }
        }

    def _upload(self, name, content, content_type=None):
        """Upload file ke Supabase Storage."""
        import urllib.request
        if content_type is None:
            content_type, _ = mimetypes.guess_type(name)
            content_type = content_type or 'application/octet-stream'

        url = f'{self.supabase_url}/storage/v1/object/{self.bucket}/{name}'
        data = content if isinstance(content, bytes) else content.read()

        req = urllib.request.Request(
            url,
            data=data,
            method='POST',
            headers={
                'Authorization': f'Bearer {self.service_key}',
                'apikey': self.service_key,
                'Content-Type': content_type,
                'x-upsert': 'true',  # overwrite jika sudah ada
            }
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status in (200, 201)
        except Exception:
            return False

    def _exists_remote(self, name):
        """Cek apakah file ada di Supabase Storage."""
        import urllib.request
        url = f'{self.supabase_url}/storage/v1/object/info/{self.bucket}/{name}'
        req = urllib.request.Request(
            url,
            headers={
                'Authorization': f'Bearer {self.service_key}',
                'apikey': self.service_key,
            }
        )
        try:
            with urllib.request.urlopen(req):
                return True
        except Exception:
            return False

    # ── Django Storage interface ──────────────────────────────────────────────

    def _save(self, name, content):
        """Simpan file ke Supabase Storage."""
        content_type, _ = mimetypes.guess_type(name)
        self._upload(name, content, content_type)
        return name

    def _open(self, name, mode='rb'):
        """Buka file dari Supabase Storage (download)."""
        import urllib.request
        import io
        url = f'{self.supabase_url}/storage/v1/object/public/{self.bucket}/{name}'
        try:
            with urllib.request.urlopen(url) as resp:
                return io.BytesIO(resp.read())
        except Exception as e:
            raise FileNotFoundError(f'File tidak ditemukan di Supabase Storage: {name}') from e

    def exists(self, name):
        return self._exists_remote(name)

    def url(self, name):
        """Return public URL file di Supabase Storage."""
        return f'{self.supabase_url}/storage/v1/object/public/{self.bucket}/{name}'

    def delete(self, name):
        import urllib.request
        url = f'{self.supabase_url}/storage/v1/object/{self.bucket}/{name}'
        req = urllib.request.Request(
            url,
            method='DELETE',
            headers={
                'Authorization': f'Bearer {self.service_key}',
                'apikey': self.service_key,
            }
        )
        try:
            urllib.request.urlopen(req)
        except Exception:
            pass

    def size(self, name):
        import urllib.request
        url = f'{self.supabase_url}/storage/v1/object/info/{self.bucket}/{name}'
        req = urllib.request.Request(
            url,
            headers={
                'Authorization': f'Bearer {self.service_key}',
                'apikey': self.service_key,
            }
        )
        try:
            with urllib.request.urlopen(req) as resp:
                import json
                data = json.loads(resp.read())
                return data.get('size', 0)
        except Exception:
            return 0

    def get_available_name(self, name, max_length=None):
        """Gunakan upsert — tidak perlu rename jika sudah ada."""
        return name
