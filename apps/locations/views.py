from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Location
from .forms import LocationForm
from .filters import LocationFilter

class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    template_name = 'locations/location_list.html'
    context_object_name = 'locations'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('parent')
        self.filterset = LocationFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context


class LocationDetailView(LoginRequiredMixin, DetailView):
    model = Location
    template_name = 'locations/location_detail.html'


class LocationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Location
    form_class = LocationForm
    template_name = 'locations/location_form.html'
    permission_required = 'locations.add_location'
    success_url = reverse_lazy('locations:location_list')

    def form_valid(self, form):
        messages.success(self.request, 'Lokasi berhasil ditambahkan.')
        return super().form_valid(form)


class LocationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = 'locations/location_form.html'
    permission_required = 'locations.change_location'
    success_url = reverse_lazy('locations:location_list')

    def form_valid(self, form):
        messages.success(self.request, 'Lokasi berhasil diperbarui.')
        return super().form_valid(form)


class LocationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Location
    success_url = reverse_lazy('locations:location_list')
    permission_required = 'locations.delete_location'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Lokasi berhasil dihapus.')
        return super().delete(request, *args, **kwargs)


class LocationHierarchyView(LoginRequiredMixin, ListView):
    model = Location
    template_name = 'locations/location_hierarchy.html'
    context_object_name = 'locations'

    def get_queryset(self):
        return Location.objects.filter(parent__isnull=True).prefetch_related('children')