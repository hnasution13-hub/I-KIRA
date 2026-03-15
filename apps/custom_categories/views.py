# ==================================================
# FILE: apps/custom_categories/views.py
# PATH: D:/Project Pyton/Asset Management Django/apps/custom_categories/views.py
# DESKRIPSI: View untuk manajemen custom kategori
# VERSION: 1.0.0
# UPDATE TERAKHIR: 05/03/2026
# ==================================================

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import CategoryCustom
from .forms import CategoryCustomForm
from apps.assets.models import Category
from .utils import generate_next_tag

class CategoryCustomListView(LoginRequiredMixin, ListView):
    model = CategoryCustom
    template_name = 'custom_categories/category_list.html'
    context_object_name = 'customs'
    paginate_by = 20

class CategoryCustomCreateView(LoginRequiredMixin, CreateView):
    model = CategoryCustom
    form_class = CategoryCustomForm
    template_name = 'custom_categories/category_form.html'
    success_url = reverse_lazy('custom_categories:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Tambah Custom Kategori'
        return context

    def form_valid(self, form):
        # Tentukan kategori berdasarkan level yang dipilih
        category = None
        if form.cleaned_data.get('category_level3'):
            category = form.cleaned_data['category_level3']
        elif form.cleaned_data.get('category_level2'):
            category = form.cleaned_data['category_level2']
        else:
            category = form.cleaned_data['category_level1']
        form.instance.category = category
        # Generate tag number jika belum ada
        if not form.instance.tag_number:
            form.instance.tag_number = generate_next_tag(category.code)
        messages.success(self.request, 'Custom kategori berhasil ditambahkan.')
        return super().form_valid(form)

class CategoryCustomUpdateView(LoginRequiredMixin, UpdateView):
    model = CategoryCustom
    form_class = CategoryCustomForm
    template_name = 'custom_categories/category_form.html'
    success_url = reverse_lazy('custom_categories:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Custom Kategori'
        return context

    def form_valid(self, form):
        # Update kategori berdasarkan pilihan
        category = None
        if form.cleaned_data.get('category_level3'):
            category = form.cleaned_data['category_level3']
        elif form.cleaned_data.get('category_level2'):
            category = form.cleaned_data['category_level2']
        else:
            category = form.cleaned_data['category_level1']
        form.instance.category = category
        messages.success(self.request, 'Custom kategori berhasil diperbarui.')
        return super().form_valid(form)

class CategoryCustomDeleteView(LoginRequiredMixin, DeleteView):
    model = CategoryCustom
    success_url = reverse_lazy('custom_categories:list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Custom kategori berhasil dihapus.')
        return super().delete(request, *args, **kwargs)

@login_required
def load_subcategories(request):
    parent_id = request.GET.get('parent_id')
    categories = Category.objects.filter(parent_id=parent_id).values('id', 'name', 'code')
    return JsonResponse(list(categories), safe=False)