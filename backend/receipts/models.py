from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ReceiptScan(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        SUCCESS = "success", _("Success")
        PARTIAL = "partial", _("Partial — low confidence")
        FAILED  = "failed",  _("Failed")

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="receipt_scans",
        verbose_name=_("Uploaded By"),
    )
    image = models.ImageField(upload_to="receipts/%Y/%m/", verbose_name=_("Receipt Image"))

    # Duplicate detection 
    image_hash = models.CharField(
        max_length=64, blank=True, default="", db_index=True,
        help_text=_("SHA-256 hex digest of uploaded image bytes."),
    )
    is_duplicate = models.BooleanField(
        default=False,
        help_text=_("True when another scan with the same image_hash already exists."),
    )

    # OCR output
    status     = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    raw_text   = models.TextField(blank=True, default="", verbose_name=_("Raw OCR Text"))
    confidence = models.FloatField(default=0.0, help_text=_("0.0–1.0 heuristic score."))

    # Extracted fields
    extracted_merchant    = models.CharField(max_length=200, blank=True, default="")
    extracted_amount      = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    extracted_currency    = models.CharField(max_length=10, blank=True, default="")
    extracted_date        = models.DateField(null=True, blank=True)
    extracted_description = models.TextField(blank=True, default="")

    # Currency conversion 
    amount_inr    = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name=_("Converted Amount (INR)"))
    exchange_rate = models.FloatField(null=True, blank=True, help_text=_("1 {currency} = X INR at scan time."))

    # Expense link 
    expense = models.OneToOneField(
        "expenses.Expense",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="receipt_scan",
        verbose_name=_("Linked Expense"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = _("Receipt Scan")
        verbose_name_plural = _("Receipt Scans")
        ordering            = ["-created_at"]

    def __str__(self):
        return f"Scan #{self.pk} | {self.uploaded_by} | {self.status} | conf={self.confidence:.0%}"


class ReceiptAudit(models.Model):
    class FraudSignal(models.TextChoices):
        NONE       = "none",       _("No discrepancy")
        AMOUNT_GAP = "amount_gap", _("Submitted amount differs from OCR")
        DUPLICATE  = "duplicate",  _("Duplicate receipt image detected")
        LOW_CONF   = "low_conf",   _("OCR confidence too low to verify")

    scan = models.OneToOneField(ReceiptScan, on_delete=models.CASCADE, related_name="audit")

    # Denormalised : avoids circular FK into expenses app
    expense_id = models.IntegerField(help_text=_("ID of the linked Expense (denormalised)."))

    ocr_amount_inr       = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    submitted_amount_inr = models.DecimalField(max_digits=14, decimal_places=2)
    discrepancy_inr      = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    discrepancy_pct      = models.FloatField(null=True, blank=True, help_text=_("Absolute % difference."))

    fraud_signal       = models.CharField(max_length=20, choices=FraudSignal.choices, default=FraudSignal.NONE, db_index=True)
    flagged_for_review = models.BooleanField(default=False, db_index=True)
    notes              = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = _("Receipt Audit")
        verbose_name_plural = _("Receipt Audits")
        ordering            = ["-created_at"]

    def __str__(self):
        return f"Audit | Scan #{self.scan_id} | Expense #{self.expense_id} | {self.fraud_signal}"