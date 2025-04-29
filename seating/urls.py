from django.urls import path
from .views import barcode_scan_view, home

urlpatterns = [
    path('', home, name='home'),
    path('scan/', barcode_scan_view, name='scan'),
]
