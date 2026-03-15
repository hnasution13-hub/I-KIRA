from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Maintenance
from .forms import MaintenanceForm
from .filters import MaintenanceFilter

class MaintenanceListView(LoginRequiredMixin, ListView):
    model = Maintenance
    template_name = 'maintenance/maintenance_list.html'
    context_object_name = 'maintenances'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('asset')
        self.filterset = MaintenanceFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context


class MaintenanceDetailView(LoginRequiredMixin, DetailView):
    model = Maintenance
    template_name = 'maintenance/maintenance_detail.html'


class MaintenanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Maintenance
    form_class = MaintenanceForm
    template_name = 'maintenance/maintenance_form.html'
    permission_required = 'maintenance.add_maintenance'
    success_url = reverse_lazy('maintenance:maintenance_list')

    def form_valid(self, form):
        messages.success(self.request, 'Jadwal maintenance berhasil ditambahkan.')
        return super().form_valid(form)


class MaintenanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Maintenance
    form_class = MaintenanceForm
    template_name = 'maintenance/maintenance_form.html'
    permission_required = 'maintenance.change_maintenance'
    success_url = reverse_lazy('maintenance:maintenance_list')

    def form_valid(self, form):
        messages.success(self.request, 'Jadwal maintenance berhasil diperbarui.')
        return super().form_valid(form)


class MaintenanceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Maintenance
    success_url = reverse_lazy('maintenance:maintenance_list')
    permission_required = 'maintenance.delete_maintenance'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Jadwal maintenance berhasil dihapus.')
        return super().delete(request, *args, **kwargs)