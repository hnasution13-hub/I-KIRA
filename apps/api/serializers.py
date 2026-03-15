from rest_framework import serializers
from apps.employees.models import Employee
from apps.attendance.models import Attendance, Leave
from apps.payroll.models import Payroll, PayrollDetail


class EmployeeSerializer(serializers.ModelSerializer):
    department_nama = serializers.StringRelatedField(source='department')
    jabatan_nama = serializers.StringRelatedField(source='jabatan')
    masa_kerja_display = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = [
            'id', 'nik', 'nama', 'department', 'department_nama',
            'jabatan', 'jabatan_nama', 'status_karyawan', 'join_date',
            'status', 'email', 'no_hp', 'masa_kerja_display',
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    employee_nama = serializers.StringRelatedField(source='employee.nama')

    class Meta:
        model = Attendance
        fields = '__all__'


class LeaveSerializer(serializers.ModelSerializer):
    employee_nama = serializers.StringRelatedField(source='employee.nama')

    class Meta:
        model = Leave
        fields = '__all__'


class PayrollDetailSerializer(serializers.ModelSerializer):
    employee_nama = serializers.StringRelatedField(source='employee.nama')

    class Meta:
        model = PayrollDetail
        fields = '__all__'


class PayrollSerializer(serializers.ModelSerializer):
    details = PayrollDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Payroll
        fields = '__all__'
