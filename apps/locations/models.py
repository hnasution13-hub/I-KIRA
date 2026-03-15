from django.db import models
from django.urls import reverse

class Location(models.Model):
    TYPE_CHOICES = [
        ('Gedung', 'Gedung'),
        ('Lantai', 'Lantai'),
        ('Ruangan', 'Ruangan'),
        ('Gudang', 'Gudang'),
        ('Area', 'Area'),
        ('Rak', 'Rak'),
        ('Lemari', 'Lemari'),
        ('Lainnya', 'Lainnya'),
    ]
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    capacity = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Lokasi'
        verbose_name_plural = 'Lokasi'

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_absolute_url(self):
        return reverse('locations:location_detail', args=[self.pk])

    def get_full_path(self):
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name