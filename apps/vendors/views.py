from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Vendor
from .forms import VendorForm
from .filters import VendorFilter

class VendorListView(LoginRequiredMixin, ListView):
    model = Vendor
    template_name = 'vendors/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = VendorFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context


class VendorDetailView(LoginRequiredMixin, DetailView):
    model = Vendor
    template_name = 'vendors/vendor_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assets'] = self.object.asset_set.all()[:20]
        return context


class VendorCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'vendors/vendor_form.html'
    permission_required = 'vendors.add_vendor'
    success_url = reverse_lazy('vendors:vendor_list')

    def form_valid(self, form):
        messages.success(self.request, 'Vendor berhasil ditambahkan.')
        return super().form_valid(form)


class VendorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'vendors/vendor_form.html'
    permission_required = 'vendors.change_vendor'
    success_url = reverse_lazy('vendors:vendor_list')

    def form_valid(self, form):
        messages.success(self.request, 'Vendor berhasil diperbarui.')
        return super().form_valid(form)


class VendorDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Vendor
    success_url = reverse_lazy('vendors:vendor_list')
    permission_required = 'vendors.delete_vendor'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Vendor berhasil dihapus.')
        return super().delete(request, *args, **kwargs)