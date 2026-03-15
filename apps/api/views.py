from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.employees.models import Employee
from apps.attendance.models import Attendance, Leave
from apps.payroll.models import Payroll, PayrollDetail
from .serializers import (
    EmployeeSerializer, AttendanceSerializer, LeaveSerializer, PayrollSerializer
)


class EmployeeViewSet(viewsets.ModelViewSet):
    # FIX BUG-016: Hapus filter status='Aktif' dari queryset agar filterset_fields
    # bisa bekerja untuk semua nilai status. Filter via ?status=Aktif di query param.
    queryset = Employee.objects.all().select_related('department', 'jabatan')
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['nama', 'nik', 'email']
    filterset_fields = ['department', 'status', 'status_karyawan']
    ordering_fields = ['nama', 'join_date']
    ordering = ['nama']

    @action(detail=True, methods=['get'])
    def salary(self, request, pk=None):
        employee = self.get_object()
        try:
            sb = employee.salary_benefit
            return Response({
                'gaji_pokok': sb.gaji_pokok,
                'total_tunjangan': sb.total_tunjangan,
                'total_take_home_pay': sb.total_take_home_pay,
            })
        except Exception:
            return Response({'error': 'Belum ada data gaji'}, status=404)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related('employee').order_by('-tanggal')
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'status', 'tanggal']


class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.select_related('employee').order_by('-created_at')
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'status', 'tipe_cuti']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'Approved'
        from django.utils import timezone
        leave.approved_at = timezone.now()
        leave.save()
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'Rejected'
        leave.save()
        return Response({'status': 'rejected'})


class PayrollViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payroll.objects.all().order_by('-periode')
    serializer_class = PayrollSerializer
    permission_classes = [IsAuthenticated]
