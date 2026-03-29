

from __future__ import annotations

import logging
from decimal import Decimal

from .models import ReceiptAudit, ReceiptScan

logger = logging.getLogger(__name__)

# Discrepancy threshold: flag if submitted amount deviates > 10% from OCR
_DISCREPANCY_THRESHOLD_PCT = 10.0
# Minimum absolute gap (INR) before flagging — avoids noise on tiny receipts
_DISCREPANCY_MIN_INR = Decimal("50.00")


def create_audit(scan: ReceiptScan, expense_id: int, submitted_amount_inr: Decimal) -> ReceiptAudit:
    existing = ReceiptAudit.objects.filter(scan=scan).first()
    if existing:
        logger.info("Audit already exists for Scan #%s — returning existing.", scan.pk)
        return existing

    signal, notes, flagged = _evaluate(scan, submitted_amount_inr)

    discrepancy_inr = None
    discrepancy_pct = None
    if scan.amount_inr is not None:
        discrepancy_inr = abs(submitted_amount_inr - scan.amount_inr)
        if scan.amount_inr > 0:
            discrepancy_pct = round(float(discrepancy_inr / scan.amount_inr * 100), 2)

    audit = ReceiptAudit.objects.create(
        scan                 = scan,
        expense_id           = expense_id,
        ocr_amount_inr       = scan.amount_inr,
        submitted_amount_inr = submitted_amount_inr,
        discrepancy_inr      = discrepancy_inr,
        discrepancy_pct      = discrepancy_pct,
        fraud_signal         = signal,
        flagged_for_review   = flagged,
        notes                = notes,
    )
    logger.info(
        "Audit created: Scan #%s → Expense #%s | signal=%s | flagged=%s",
        scan.pk, expense_id, signal, flagged,
    )
    return audit


def _evaluate(
    scan: ReceiptScan,
    submitted_amount_inr: Decimal,
) -> tuple[str, str, bool]:
    """
    Returns (fraud_signal, notes, flagged_for_review).
    Priority: DUPLICATE > AMOUNT_GAP > LOW_CONF > NONE
    """

    if scan.is_duplicate:
        return (
            ReceiptAudit.FraudSignal.DUPLICATE,
            "This image hash matches a previously uploaded receipt.",
            True,
        )

    if scan.confidence < 0.3:
        return (
            ReceiptAudit.FraudSignal.LOW_CONF,
            f"OCR confidence {scan.confidence:.0%} is too low to verify amount.",
            False,
        )

    if scan.amount_inr is None:
        return (
            ReceiptAudit.FraudSignal.NONE,
            "No OCR amount available for comparison.",
            False,
        )

    gap = abs(submitted_amount_inr - scan.amount_inr)
    if scan.amount_inr > 0:
        pct = float(gap / scan.amount_inr * 100)
    else:
        pct = 0.0

    if gap >= _DISCREPANCY_MIN_INR and pct >= _DISCREPANCY_THRESHOLD_PCT:
        return (
            ReceiptAudit.FraudSignal.AMOUNT_GAP,
            (
                f"Submitted ₹{submitted_amount_inr} vs OCR ₹{scan.amount_inr}. "
                f"Gap: ₹{gap} ({pct:.1f}%)."
            ),
            True,
        )

    return ReceiptAudit.FraudSignal.NONE, "", False