# ==================================================
# FILE: apps/audit/views.py
# PERBAIKAN: Fix import pytz -> django.utils.timezone, fix models.Count
# ==================================================

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count

from .models import AuditLog
from .forms import AuditLogFilterForm


class AuditLogListView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = 'audit/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user')
        form = AuditLogFilterForm(self.request.GET)
        if form.is_valid():
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            username = form.cleaned_data.get('username')
            action = form.cleaned_data.get('action')
            if date_from:
                queryset = queryset.filter(timestamp__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(timestamp__date__lte=date_to)
            if username:
                queryset = queryset.filter(username__icontains=username)
            if action:
                queryset = queryset.filter(action=action)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = AuditLogFilterForm(self.request.GET)
        return context


class AuditLogDetailView(LoginRequiredMixin, DetailView):
    model = AuditLog
    template_name = 'audit/log_detail.html'


@login_required
def statistics_view(request):
    total = AuditLog.objects.count()
    today = AuditLog.objects.filter(timestamp__date=timezone.now().date()).count()
    by_action = AuditLog.objects.values('action').annotate(count=Count('id')).order_by('-count')
    context = {
        'total': total,
        'today': today,
        'by_action': by_action,
    }
    return render(request, 'audit/statistics.html', context)
