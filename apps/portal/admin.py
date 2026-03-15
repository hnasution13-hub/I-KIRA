from django.contrib import admin
from .models import BiodataChangeLog


@admin.register(BiodataChangeLog)
class BiodataChangeLogAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'label', 'nilai_lama', 'nilai_baru', 'user', 'waktu')
    list_filter   = ('waktu',)
    search_fields = ('employee__nama', 'employee__nik', 'label', 'field_name')
    readonly_fields = ('employee', 'user', 'field_name', 'label', 'nilai_lama', 'nilai_baru', 'waktu')
    ordering      = ('-waktu',)

    def has_add_permission(self, request):
        return False  # Log hanya dibuat otomatis oleh sistem

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
