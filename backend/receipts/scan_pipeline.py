from __future__ import annotations

import logging

from .currency_service import CurrencyError, convert_to_inr
from .ocr_service import extract_from_image
from .models import ReceiptScan

logger = logging.getLogger(__name__)

# Thresholds (tune without touching view logic)
_CONFIDENCE_SUCCESS = 0.7
_CONFIDENCE_PARTIAL = 0.3


def run_scan_pipeline(scan_id: int, currency_hint: str = "") -> ReceiptScan:
    try:
        scan = ReceiptScan.objects.get(pk=scan_id)
    except ReceiptScan.DoesNotExist:
        logger.error("run_scan_pipeline: ReceiptScan #%s not found.", scan_id)
        raise

    scan.status = ReceiptScan.Status.PENDING
    scan.save(update_fields=["status"])

    try:
        ocr = extract_from_image(scan.image.path)

        scan.raw_text              = ocr.raw_text
        scan.confidence            = ocr.confidence
        scan.extracted_merchant    = (ocr.merchant or "")[:200]
        scan.extracted_description = ocr.description or ""

        if ocr.date:
            scan.extracted_date = ocr.date

        if ocr.amount:
            try:
                scan.extracted_amount = float(ocr.amount)
            except (ValueError, TypeError):
                logger.warning("Scan #%s: could not cast OCR amount '%s'", scan_id, ocr.amount)

        detected_currency = (ocr.currency_code or currency_hint or "").upper().strip()
        if detected_currency:
            scan.extracted_currency = detected_currency

        if scan.extracted_amount and detected_currency:
            try:
                inr, rate = convert_to_inr(float(scan.extracted_amount), detected_currency)
                scan.amount_inr    = inr
                scan.exchange_rate = rate
            except CurrencyError as exc:
                logger.warning("Scan #%s: currency conversion skipped — %s", scan_id, exc)

        if scan.confidence >= _CONFIDENCE_SUCCESS:
            scan.status = ReceiptScan.Status.SUCCESS
        elif scan.confidence >= _CONFIDENCE_PARTIAL:
            scan.status = ReceiptScan.Status.PARTIAL
        else:
            scan.status = ReceiptScan.Status.FAILED

    except Exception:
        logger.exception("Scan pipeline failed for ReceiptScan #%s", scan_id)
        scan.status = ReceiptScan.Status.FAILED

    scan.save(update_fields=[
        "status", "raw_text", "confidence",
        "extracted_merchant", "extracted_description",
        "extracted_date", "extracted_amount", "extracted_currency",
        "amount_inr", "exchange_rate",
    ])
    return scan