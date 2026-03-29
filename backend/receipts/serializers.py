

from django.conf import settings
from rest_framework import serializers

from .models import ReceiptAudit, ReceiptScan

_MAX_MB = getattr(settings, "RECEIPT_MAX_UPLOAD_MB", 10)
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/tiff"}
_ALLOWED_EXTENSIONS    = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


class ScanUploadSerializer(serializers.Serializer):
    """Input for POST /api/receipts/scan/"""

    image = serializers.ImageField(required=True)
    currency_hint = serializers.CharField(
        required=False, max_length=10, default="",
        help_text="Optional ISO 4217 fallback (e.g. 'USD').",
    )

    def validate_image(self, image_file):
        max_bytes = _MAX_MB * 1024 * 1024
        if image_file.size > max_bytes:
            raise serializers.ValidationError(
                f"File too large. Maximum allowed size is {_MAX_MB} MB."
            )

        content_type = getattr(image_file, "content_type", "")
        if content_type and content_type not in _ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError(
                f"Unsupported file type '{content_type}'. Allowed: JPEG, PNG, WebP, TIFF."
            )

        import os
        ext = os.path.splitext(image_file.name)[1].lower()
        if ext and ext not in _ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported extension '{ext}'. Allowed: .jpg .jpeg .png .webp .tif .tiff"
            )

        return image_file


class ReceiptAuditSerializer(serializers.ModelSerializer):
    fraud_signal_display = serializers.CharField(source="get_fraud_signal_display", read_only=True)

    class Meta:
        model  = ReceiptAudit
        fields = [
            "id", "expense_id",
            "ocr_amount_inr", "submitted_amount_inr",
            "discrepancy_inr", "discrepancy_pct",
            "fraud_signal", "fraud_signal_display",
            "flagged_for_review", "notes", "created_at",
        ]
        read_only_fields = fields


class ReceiptScanSerializer(serializers.ModelSerializer):
    """Read-only output after upload and retry."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    audit          = ReceiptAuditSerializer(read_only=True)

    class Meta:
        model  = ReceiptScan
        fields = [
            "id",
            "status", "status_display",
            "confidence",
            "is_duplicate",
            "extracted_merchant",
            "extracted_amount", "extracted_currency",
            "extracted_date",
            "extracted_description",
            "amount_inr", "exchange_rate",
            "expense",
            "audit",
            "created_at",
        ]
        read_only_fields = fields


class LinkExpenseSerializer(serializers.Serializer):
    """
    Validates receipt_scan_id when passed during POST /api/expenses/.
    Imported by the expenses app view — zero model-level coupling to receipts.
    """
    receipt_scan_id = serializers.IntegerField(required=False, allow_null=True, default=None)

    def validate_receipt_scan_id(self, value):
        if value is None:
            return None
        request = self.context.get("request")
        try:
            scan = ReceiptScan.objects.get(pk=value)
        except ReceiptScan.DoesNotExist:
            raise serializers.ValidationError(f"ReceiptScan #{value} does not exist.")
        if request and scan.uploaded_by_id != request.user.pk:
            raise serializers.ValidationError("You can only link your own receipt scans.")
        if scan.expense_id is not None:
            raise serializers.ValidationError(
                f"ReceiptScan #{value} is already linked to Expense #{scan.expense_id}."
            )
        return value


class CurrencySerializer(serializers.Serializer):
    code   = serializers.CharField()
    name   = serializers.CharField()
    symbol = serializers.CharField()