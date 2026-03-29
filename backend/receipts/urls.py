

from django.urls import path

from .views import (
    CurrencyConvertView,
    CurrencyListView,
    ReceiptScanRetryView,
    ReceiptScanView,
)

urlpatterns = [
    path("scan/",            ReceiptScanView.as_view(),       name="receipt-scan"),
    path("<int:pk>/retry/",  ReceiptScanRetryView.as_view(),  name="receipt-retry"),
    path("currencies/",      CurrencyListView.as_view(),      name="currency-list"),
    path("convert/",         CurrencyConvertView.as_view(),   name="currency-convert"),
]