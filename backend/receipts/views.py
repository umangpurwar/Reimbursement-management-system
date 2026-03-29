from __future__ import annotations

import hashlib
import logging
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .audit_service import create_audit
from .currency_service import CurrencyError, convert_to_inr, get_supported_currencies
from .models import ReceiptScan
from .scan_pipeline import run_scan_pipeline
from .serializers import (
    CurrencySerializer,
    ReceiptScanSerializer,
    ScanUploadSerializer,
)

logger = logging.getLogger(__name__)


def _sha256(file_obj) -> str:
    file_obj.seek(0)
    digest = hashlib.sha256(file_obj.read()).hexdigest()
    file_obj.seek(0)
    return digest


def _check_duplicate(image_hash: str, uploader_id: int) -> bool:
    return ReceiptScan.objects.filter(image_hash=image_hash).exclude(
        uploaded_by_id=uploader_id, status=ReceiptScan.Status.PENDING
    ).exists()


class ReceiptScanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        upload_ser = ScanUploadSerializer(data=request.data)
        upload_ser.is_valid(raise_exception=True)

        image_file = upload_ser.validated_data["image"]
        currency_hint = upload_ser.validated_data.get("currency_hint", "").upper().strip()

        image_hash = _sha256(image_file)
        is_dup = _check_duplicate(image_hash, request.user.pk)

        scan = ReceiptScan(
            uploaded_by=request.user,
            image=image_file,
            image_hash=image_hash,
            is_duplicate=is_dup,
            status=ReceiptScan.Status.PENDING,
        )
        scan.save()

        scan = run_scan_pipeline(scan.pk, currency_hint)

        out = ReceiptScanSerializer(scan, context={"request": request})
        http_status = (
            status.HTTP_200_OK
            if scan.status in {ReceiptScan.Status.SUCCESS, ReceiptScan.Status.PARTIAL}
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return Response(out.data, status=http_status)


class ReceiptScanRetryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int):
        scan = get_object_or_404(ReceiptScan, pk=pk, uploaded_by=request.user)

        if scan.status not in {ReceiptScan.Status.FAILED, ReceiptScan.Status.PARTIAL}:
            return Response(
                {
                    "detail": (
                        f"Scan #{pk} has status '{scan.status}' and cannot be retried. "
                        f"Only 'failed' or 'partial' scans can be retried."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        currency_hint = str(request.data.get("currency_hint", "")).upper().strip()
        scan = run_scan_pipeline(scan.pk, currency_hint)

        out = ReceiptScanSerializer(scan, context={"request": request})
        return Response(out.data, status=status.HTTP_200_OK)


class CurrencyListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            currencies = get_supported_currencies()
        except Exception as e:
            logger.error("Currency list fetch failed: %s", e)
            return Response(
                {"detail": "Unable to fetch currency list. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(CurrencySerializer(currencies, many=True).data)


class CurrencyConvertView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        raw_amount = request.data.get("amount")
        currency = str(request.data.get("currency", "")).upper().strip()

        if not raw_amount or not currency:
            return Response(
                {"detail": "Both 'amount' and 'currency' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            amount = float(raw_amount)
        except (TypeError, ValueError):
            return Response(
                {"detail": "'amount' must be a valid number."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if amount <= 0:
            return Response(
                {"detail": "'amount' must be greater than zero."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            inr, rate = convert_to_inr(amount, currency)
        except CurrencyError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "amount_original": amount,
            "currency": currency,
            "amount_inr": inr,
            "exchange_rate": rate,
            "note": f"1 {currency} = {rate} INR",
        })


@transaction.atomic
def link_scan_to_expense(scan_id: int, expense, submitted_amount_inr: Decimal) -> None:
    try:
        scan = ReceiptScan.objects.select_for_update().get(pk=scan_id)
    except ReceiptScan.DoesNotExist:
        logger.error("link_scan_to_expense: ReceiptScan #%s not found.", scan_id)
        return

    if scan.expense_id == expense.pk:
        return

    if scan.expense_id is not None:
        logger.warning(
            "Scan #%s already linked to Expense #%s — skipping link to Expense #%s.",
            scan_id, scan.expense_id, expense.pk,
        )
        return

    scan.expense = expense
    scan.save(update_fields=["expense", "updated_at"])

    create_audit(scan, expense.pk, submitted_amount_inr)

    logger.info("Scan #%s linked to Expense #%s.", scan_id, expense.pk)