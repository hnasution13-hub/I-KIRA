from django.contrib import admin
from django.http import JsonResponse

def views_ping(request):
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ok', 'db': 'ok', 'app': 'Ikira HRIS'})
    except Exception as e:
        return JsonResponse({'status': 'ok', 'db': 'error', 'detail': str(e)})
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
import os

urlpatterns = [
    path('ping/', views_ping, name='ping'),
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),

    # ── Password Reset (standalone, tidak konflik dengan login/logout kustom) ──
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

    path('employees/', include('apps.employees.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('contracts/', include('apps.contracts.urls')),
    path('payroll/', include('apps.payroll.urls')),
    path('industrial/', include('apps.industrial.urls')),
    path('recruitment/', include('apps.recruitment.urls')),
    path('psychotest/',  include('apps.psychotest.urls')),
    path('advanced-test/', include('apps.advanced_psychotest.urls')),
    path('reports/', include('apps.reports.urls')),
    path('api/', include('apps.api.urls')),
    path('wilayah/', include('apps.wilayah.urls')),
    # ── Add-On: Asset Management ─────────────────────────
    path('asset/',       include('apps.assets.urls')),
    path('locations/',   include('apps.locations.urls')),
    path('vendors/',     include('apps.vendors.urls')),
    path('movements/',   include('apps.movements.urls')),
    path('maintenance/', include('apps.maintenance.urls')),
    path('audit-asset/', include('apps.audit.urls')),
    path('asset-reports/', include('apps.asset_reports.urls')),
    path('custom-categories/', include('apps.custom_categories.urls')),
    path('karyawan/', include('apps.portal.urls')),
    path('shifts/', include('apps.shifts.urls')),
    # ── Add-On: Organisation Development ─────────────────
    path('od/', include('apps.od.urls')),
    path('performance/', include('apps.performance.urls')),
    # ── Registrasi Demo & Trial ───────────────────────────
    path('daftar/', include('apps.registration.urls')),
    # ── Investor Dashboard ────────────────────────────────
    path('investor/', include('apps.investor.urls')),
    # ── API Docs (drf-spectacular) ────────────────────────
    path('api/docs/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('qa-full/', include('apps.core.urls_qa')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'apps.core.views.error_403'
handler404 = 'apps.core.views.error_404'
handler500 = 'apps.core.views.error_500'