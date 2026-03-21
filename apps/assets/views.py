# ==================================================
# FILE: apps/assets/views.py
# PERBAIKAN: Fix status filter sesuai model (ACTIVE, MAINTENANCE, RETIRED, BROKEN, RESERVED)
# VERSION: 1.0.2
# ==================================================

import logging

logger = logging.getLogger(__name__)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from apps.core.addon_decorators import addon_required, _is_addon_active, ADDON_LABELS


class AddonRequiredMixin:
    addon_name = 'assets'

    def dispatch(self, request, *args, **kwargs):
        from django.shortcuts import render
        if not getattr(request, 'is_developer', False):
            company = getattr(request, 'company', None)
            if not _is_addon_active(company, self.addon_name):
                return render(request, 'core/addon_locked.html', {
                    'addon_name':  self.addon_name,
                    'addon_label': ADDON_LABELS.get(self.addon_name, self.addon_name),
                })
        return super().dispatch(request, *args, **kwargs)


from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Asset, Category
from .forms import AssetForm, CategoryForm
from .filters import AssetFilter


def _get_company(request):
    """Helper multi-tenant — fallback ke Company.objects.first() untuk superuser."""
    from apps.core.models import Company
    company = getattr(request, 'company', None)
    if not company and getattr(request.user, 'is_superuser', False):
        company = Company.objects.first()
    return company


class AssetListView(AddonRequiredMixin, LoginRequiredMixin, ListView):
    model = Asset
    template_name = 'assets/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 20

    def get_queryset(self):
        company = _get_company(self.request)
        queryset = Asset.objects.select_related(
            'category', 'location', 'vendor', 'responsible'
        )
        if company:
            queryset = queryset.filter(company=company)
        self.filterset = AssetFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = _get_company(self.request)
        qs = Asset.objects.filter(company=company) if company else Asset.objects
        context['filter'] = self.filterset
        context['total_assets'] = qs.count()
        context['active_count'] = qs.filter(status='ACTIVE').count()
        context['maintenance_count'] = qs.filter(status='MAINTENANCE').count()
        context['retired_count'] = qs.filter(status='RETIRED').count()
        context['broken_count'] = qs.filter(status='BROKEN').count()
        return context


class AssetDetailView(AddonRequiredMixin, LoginRequiredMixin, DetailView):
    model = Asset
    template_name = 'assets/asset_detail.html'
    context_object_name = 'asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['movements'] = self.object.movements.all().order_by('-movement_date')[:10]
        context['maintenances'] = self.object.maintenances.all().order_by('-maintenance_date')[:5]
        context['depreciations'] = self.object.depreciation_set.all().order_by('-year', '-month')[:12]
        return context


class AssetCreateView(AddonRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    permission_required = 'assets.add_asset'
    success_url = reverse_lazy('assets:asset_list')

    def form_valid(self, form):
        form.instance.company = _get_company(self.request)
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        try:
            from .depreciation import generate_depreciation
            generate_depreciation(self.object)
        except Exception as e:
            logger.warning(f'generate_depreciation gagal untuk {self.object.asset_code}: {e}')
        messages.success(self.request, f'Asset {self.object.asset_code} berhasil ditambahkan.')
        return response


class AssetUpdateView(AddonRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    permission_required = 'assets.change_asset'
    success_url = reverse_lazy('assets:asset_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        try:
            from .depreciation import generate_depreciation
            generate_depreciation(self.object)
        except Exception as e:
            logger.warning(f'generate_depreciation gagal untuk {self.object.asset_code}: {e}')
        messages.success(self.request, f'Asset {self.object.asset_code} berhasil diperbarui.')
        return response


class AssetDeleteView(AddonRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Asset
    template_name = 'assets/asset_confirm_delete.html'
    success_url = reverse_lazy('assets:asset_list')
    permission_required = 'assets.delete_asset'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Asset berhasil dihapus.')
        return super().delete(request, *args, **kwargs)


# Category Views
class CategoryListView(AddonRequiredMixin, LoginRequiredMixin, ListView):
    model = Category
    template_name = 'assets/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        company = _get_company(self.request)
        qs = Category.objects.filter(parent__isnull=True).prefetch_related('children')
        if company:
            qs = qs.filter(company=company)
        return qs


class CategoryDetailView(AddonRequiredMixin, LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'assets/category_detail.html'
    context_object_name = 'category'

    def get_queryset(self):
        company = _get_company(self.request)
        qs = Category.objects.all()
        if company:
            qs = qs.filter(company=company)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assets'] = self.object.asset_set.all()[:20]
        context['subcategories'] = self.object.children.all()
        return context


class CategoryCreateView(AddonRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'assets/category_form.html'
    permission_required = 'assets.add_category'
    success_url = reverse_lazy('assets:category_list')

    def form_valid(self, form):
        form.instance.company = _get_company(self.request)
        messages.success(self.request, 'Kategori berhasil ditambahkan.')
        return super().form_valid(form)


class CategoryUpdateView(AddonRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'assets/category_form.html'
    permission_required = 'assets.change_category'
    success_url = reverse_lazy('assets:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Kategori berhasil diperbarui.')
        return super().form_valid(form)


class CategoryDeleteView(AddonRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Category
    template_name = 'assets/category_confirm_delete.html'
    success_url = reverse_lazy('assets:category_list')
    permission_required = 'assets.delete_category'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Kategori berhasil dihapus.')
        return super().delete(request, *args, **kwargs)


class CategoryHierarchyView(AddonRequiredMixin, LoginRequiredMixin, ListView):
    model = Category
    template_name = 'assets/category_hierarchy.html'
    context_object_name = 'categories'

    def get_queryset(self):
        company = _get_company(self.request)
        qs = Category.objects.filter(parent__isnull=True).prefetch_related('children')
        if company:
            qs = qs.filter(company=company)
        return qs


# ── Import Bulk ───────────────────────────────────────────────────────────────

@login_required
@addon_required('assets')
def download_template_asset(request):
    from .export_import import download_template_import_asset
    company = _get_company(request)
    return download_template_import_asset(company=company)


@login_required
@addon_required('assets')
def import_asset(request):
    from apps.core.models import Company as CoreCompany
    is_developer = getattr(request, 'is_developer', False)
    companies    = CoreCompany.objects.filter(status__in=['aktif', 'trial', 'demo']).order_by('nama') if is_developer else None

    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'Pilih file Excel terlebih dahulu.')
            return render(request, 'assets/asset_import.html', {
                'is_developer': is_developer, 'companies': companies,
            })

        file = request.FILES['file']
        if not file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Format file harus .xlsx atau .xls')
            return render(request, 'assets/asset_import.html', {
                'is_developer': is_developer, 'companies': companies,
            })

        from .export_import import import_asset_excel
        company = _get_company(request)

        if is_developer:
            company_id = request.POST.get('company_id')
            if not company_id:
                messages.error(request, 'Pilih Company tujuan import terlebih dahulu.')
                return render(request, 'assets/asset_import.html', {
                    'is_developer': is_developer, 'companies': companies,
                })
            try:
                company = CoreCompany.objects.get(pk=company_id)
            except CoreCompany.DoesNotExist:
                messages.error(request, 'Company tidak ditemukan.')
                return render(request, 'assets/asset_import.html', {
                    'is_developer': is_developer, 'companies': companies,
                })

        if not company:
            messages.error(request, 'Company tidak terdeteksi. Hubungi Developer.')
            return render(request, 'assets/asset_import.html', {
                'is_developer': is_developer, 'companies': companies,
            })

        success_count, errors = import_asset_excel(file, company)

        if success_count:
            messages.success(request, f'{success_count} aset berhasil diimport ke {company.nama}.')

        for err in errors:
            baris  = err.get('baris', '-')
            nama   = err.get('nama', '-') or '-'
            alasan = err.get('alasan', '')
            messages.warning(request, f'Baris {baris} | {nama} → {alasan}')

        return redirect('assets:asset_import')

    return render(request, 'assets/asset_import.html', {
        'is_developer': is_developer,
        'companies':    companies,
    })
