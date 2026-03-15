"""
Tambahkan endpoint /ping/ ke hris_project/urls.py
Endpoint ini yang akan di-ping oleh cron-job.org setiap 10 menit
supaya Render tidak auto-sleep.

Cara tambahkan ke urls.py:
    from django.http import JsonResponse
    path('ping/', lambda r: JsonResponse({'status': 'ok'}), name='ping'),
"""
