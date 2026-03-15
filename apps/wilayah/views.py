from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Provinsi, Kabupaten, Kecamatan, Kelurahan


@login_required
def api_search_kabupaten(request):
    """Search kabupaten/kota by nama — untuk autocomplete tempat lahir."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    qs = Kabupaten.objects.filter(nama__icontains=q).select_related('provinsi').order_by('nama')[:20]
    data = [{'id': k.id, 'text': f"{k.nama} ({k.provinsi.nama})"} for k in qs]
    return JsonResponse({'results': data})


@login_required
def api_provinsi(request):
    """Return semua provinsi."""
    data = list(Provinsi.objects.values('id', 'kode', 'nama'))
    return JsonResponse(data, safe=False)


@login_required
def api_kabupaten(request):
    """Return kabupaten berdasarkan provinsi_id."""
    provinsi_id = request.GET.get('provinsi_id')
    if not provinsi_id:
        return JsonResponse([], safe=False)
    data = list(Kabupaten.objects.filter(provinsi_id=provinsi_id).values('id', 'kode', 'nama'))
    return JsonResponse(data, safe=False)


@login_required
def api_kecamatan(request):
    """Return kecamatan berdasarkan kabupaten_id."""
    kabupaten_id = request.GET.get('kabupaten_id')
    if not kabupaten_id:
        return JsonResponse([], safe=False)
    data = list(Kecamatan.objects.filter(kabupaten_id=kabupaten_id).values('id', 'kode', 'nama'))
    return JsonResponse(data, safe=False)


@login_required
def api_kelurahan(request):
    """Return kelurahan berdasarkan kecamatan_id."""
    kecamatan_id = request.GET.get('kecamatan_id')
    if not kecamatan_id:
        return JsonResponse([], safe=False)
    data = list(Kelurahan.objects.filter(kecamatan_id=kecamatan_id).values('id', 'kode', 'nama', 'kode_pos'))
    return JsonResponse(data, safe=False)


@login_required
def api_bank(request):
    """Return semua bank — untuk select2/autocomplete di form karyawan."""
    from .models import Bank
    q = request.GET.get('q', '').strip()
    qs = Bank.objects.all().order_by('nama')
    if q:
        qs = qs.filter(nama__icontains=q)
    data = [{'id': b.id, 'kode': b.kode, 'text': b.nama} for b in qs[:50]]
    return JsonResponse({'results': data})
