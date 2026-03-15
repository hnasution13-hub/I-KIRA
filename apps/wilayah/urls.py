from django.urls import path
from . import views

urlpatterns = [
    path('provinsi/',          views.api_provinsi,          name='api_provinsi'),
    path('kabupaten/',         views.api_kabupaten,         name='api_kabupaten'),
    path('kecamatan/',         views.api_kecamatan,         name='api_kecamatan'),
    path('kelurahan/',         views.api_kelurahan,         name='api_kelurahan'),
    path('search/kabupaten/',  views.api_search_kabupaten,  name='api_search_kabupaten'),
    path('bank/',              views.api_bank,              name='api_bank'),
]
