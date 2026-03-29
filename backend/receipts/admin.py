# receipts/admin.py

from django.contrib import admin
from .models import ReceiptAudit, ReceiptScan


class ReceiptAuditInline(admin.StackedInline):
    model       = ReceiptAudit
    extra       = 0
    can_delete  = False
    readonly_fields = (
        "expense_id", "ocr_amount_inr", "submitted_amount_inr",
        "discrepancy_inr", "discrepancy_pct",
        "fraud_signal", "flagged_for_review", "notes", "created_at",
    )


@admin.register(ReceiptScan)
class ReceiptScanAdmin(admin.ModelAdmin):
    list_display = (
        "id", "uploaded_by", "status", "confidence",
        "is_duplicate", "extracted_currency", "amount_inr",
        "expense", "created_at",
    )
    list_filter   = ("status", "is_duplicate", "extracted_currency")
    search_fields = ("uploaded_by__username", "extracted_merchant", "image_hash")
    readonly_fields = (
        "image_hash", "is_duplicate",
        "raw_text", "extracted_merchant", "extracted_amount",
        "extracted_currency", "extracted_date", "extracted_description",
        "amount_inr", "exchange_rate", "confidence", "status",
        "created_at", "updated_at",
    )
    inlines  = [ReceiptAuditInline]
    ordering = ("-created_at",)


@admin.register(ReceiptAudit)
class ReceiptAuditAdmin(admin.ModelAdmin):
    list_display = (
        "id", "scan", "expense_id", "fraud_signal",
        "flagged_for_review", "discrepancy_pct", "created_at",
    )
    list_filter   = ("fraud_signal", "flagged_for_review")
    search_fields = ("scan__uploaded_by__username",)
    readonly_fields = (
        "scan", "expense_id",
        "ocr_amount_inr", "submitted_amount_inr",
        "discrepancy_inr", "discrepancy_pct",
        "fraud_signal", "flagged_for_review", "notes", "created_at",
    )
    ordering = ("-created_at",)