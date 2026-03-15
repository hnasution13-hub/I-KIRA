# ==================================================
# FILE: apps/movements/views.py
# PATH: D:/Project Pyton/Asset Management Django/apps/movements/views.py
# DESKRIPSI: View untuk mutasi aset dan penugasan
# PERBAIKAN: Update assignment dengan benar, tambah validasi
# VERSION: 1.0.1
# UPDATE TERAKHIR: 05/03/2026
# ==================================================

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Movement, Assignment
from .forms import MovementForm, AssignmentForm
from .filters import MovementFilter, AssignmentFilter

class MovementListView(LoginRequiredMixin, ListView):
    model = Movement
    template_name = 'movements/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('asset', 'from_pic', 'to_pic', 'from_location', 'to_location')
        self.filterset = MovementFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context


class MovementDetailView(LoginRequiredMixin, DetailView):
    model = Movement
    template_name = 'movements/movement_detail.html'


class MovementCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Movement
    form_class = MovementForm
    template_name = 'movements/movement_form.html'
    permission_required = 'movements.add_movement'
    success_url = reverse_lazy('movements:movement_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self.update_assignment()
        messages.success(self.request, 'Mutasi berhasil dicatat.')
        return response

    def update_assignment(self):
        """Update atau buat assignment terkini berdasarkan movement yang baru."""
        movement = self.object
        asset = movement.asset
        assignment, created = Assignment.objects.get_or_create(asset=asset)
        assignment.current_pic = movement.to_pic
        assignment.current_pic_name = movement.to_pic_name
        assignment.current_location = movement.to_location
        assignment.current_location_name = movement.to_location_name
        assignment.current_condition = movement.to_condition
        assignment.assignment_date = movement.movement_date
        assignment.last_movement = movement
        assignment.last_movement_date = movement.movement_date
        # Jika tipe movement adalah penugasan dan ada expected return date (perlu tambah field di form)
        if movement.movement_type == 'PENUGASAN' and hasattr(movement, 'expected_return_date'):
            assignment.expected_return_date = movement.expected_return_date
        assignment.save()


class MovementUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Movement
    form_class = MovementForm
    template_name = 'movements/movement_form.html'
    permission_required = 'movements.change_movement'
    success_url = reverse_lazy('movements:movement_list')

    def form_valid(self, form):
        messages.success(self.request, 'Mutasi berhasil diperbarui.')
        return super().form_valid(form)


class MovementDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Movement
    success_url = reverse_lazy('movements:movement_list')
    permission_required = 'movements.delete_movement'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Mutasi berhasil dihapus.')
        return super().delete(request, *args, **kwargs)


class AssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = 'movements/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('asset', 'current_pic', 'current_location')
        self.filterset = AssignmentFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context


class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = Assignment
    template_name = 'movements/assignment_detail.html'