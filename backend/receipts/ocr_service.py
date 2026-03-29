from __future__ import annotations
import io
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


  
# Result dataclass
  

@dataclass
class OCRResult:
    raw_text: str = ""
    amount: Optional[str] = None          # e.g. "1250.00"
    currency_code: Optional[str] = None   # e.g. "USD", "INR"
    date: Optional[str] = None            # ISO 8601: "2026-03-29"
    merchant: Optional[str] = None        # e.g. "Starbucks"
    description: Optional[str] = None     # e.g. "Coffee x2, Muffin"
    confidence: float = 0.0               # 0.0–1.0, rough heuristic

    def to_dict(self) -> dict:
        return {
            "raw_text":      self.raw_text,
            "amount":        self.amount,
            "currency_code": self.currency_code,
            "date":          self.date,
            "merchant":      self.merchant,
            "description":   self.description,
            "confidence":    round(self.confidence, 2),
        }


  
# Regex patterns
  

# Amount — matches patterns like:  $1,250.00  |  INR 5,000  |  1250.50  |  Rs.450
_AMOUNT_RE = re.compile(
    r"""
    (?:                          # optional currency prefix
        (?P<prefix_sym>[₹$€£¥])  # unicode symbols
        |
        (?P<prefix_code>INR|USD|EUR|GBP|JPY|AED|SGD|AUD|CAD|CHF)\s*
        |
        (?:Rs\.?\s*)
    )?
    (?P<amount>
        \d{1,3}(?:[,\s]\d{3})*  # thousands-grouped
        (?:\.\d{1,2})?           # optional decimal
        |
        \d+\.\d{1,2}             # simple decimal
    )
    (?:\s*(?P<suffix_code>INR|USD|EUR|GBP|JPY|AED|SGD|AUD|CAD|CHF))?
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Date — common receipt formats
_DATE_RES = [
    re.compile(r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b"),          # 2026-03-29
    re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b"),        # 29/03/2026 or 03/29/26
    re.compile(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{2,4})\b"),    # 29 March 2026
    re.compile(r"\b([A-Za-z]{3,9})\s+(\d{1,2})[,\s]+(\d{2,4})\b"), # March 29, 2026
]

_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4,
    "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}

# Currency symbols → ISO codes
_SYM_TO_CODE = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR"}

# Lines that suggest totals (picked over subtotals / line items)
_TOTAL_KEYWORDS = re.compile(
    r"\b(grand\s+total|total\s+amount|total\s+due|amount\s+due|net\s+total|total)\b",
    re.IGNORECASE,
)


  
# Public API
  

def extract_from_image(image_source) -> OCRResult:
    """
    Main entry point.

    Args:
        image_source: file path (str/Path), raw bytes, or a PIL.Image.Image

    Returns:
        OCRResult — never raises; logs errors and returns empty result.
    """
    try:
        import pytesseract
        
        from PIL import Image, ImageEnhance, ImageFilter

        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    except ImportError as e:
        logger.error("pytesseract/Pillow not installed: %s", e)
        return OCRResult(raw_text="[OCR unavailable — pytesseract not installed]")

    try:
        img = _load_image(image_source)
        img = _preprocess(img)
        raw = pytesseract.image_to_string(img, config="--psm 6")
    except Exception as e:
        logger.exception("OCR extraction failed: %s", e)
        return OCRResult(raw_text=f"[OCR error: {e}]")

    return _parse(raw)


def extract_from_django_file(django_file) -> OCRResult:
    """
    Convenience wrapper for Django InMemoryUploadedFile / TemporaryUploadedFile.
    """
    return extract_from_image(django_file.read())


  
# Internal helpers


def _load_image(source):
    from PIL import Image
    if isinstance(source, bytes):
        return Image.open(io.BytesIO(source)).convert("RGB")
    if hasattr(source, "read"):
        return Image.open(source).convert("RGB")
    return Image.open(source).convert("RGB")


def _preprocess(img):
    """
    Basic image cleanup that significantly improves OCR accuracy on receipts:
    - Convert to greyscale
    - Sharpen edges
    - Boost contrast
    """
    from PIL import ImageEnhance, ImageFilter, ImageOps
    img = img.convert("L")                          # greyscale
    img = img.filter(ImageFilter.SHARPEN)           # sharpen
    img = ImageOps.autocontrast(img)                # auto contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    return img


def _parse(raw_text: str) -> OCRResult:
    result = OCRResult(raw_text=raw_text)
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

    result.merchant   = _extract_merchant(lines)
    result.date       = _extract_date(raw_text)
    amount, currency  = _extract_amount(lines, raw_text)
    result.amount     = amount
    result.currency_code = currency
    result.description = _extract_description(lines)
    result.confidence  = _compute_confidence(result)

    return result


def _extract_merchant(lines: list[str]) -> Optional[str]:
    """
    The merchant name is almost always in the first 1-3 non-blank lines,
    before any item/price data begins. We take the first line that is mostly
    alpha (not a date, not a number-heavy line).
    """
    for line in lines[:5]:
        clean = line.strip()
        if not clean:
            continue
        digit_ratio = sum(c.isdigit() for c in clean) / max(len(clean), 1)
        if digit_ratio < 0.3 and len(clean) >= 3:
            # Filter out generic receipt headers
            if not re.search(r"\b(receipt|invoice|bill|tax|gst|vat)\b", clean, re.I):
                return clean[:80]
    return None


def _extract_date(text: str) -> Optional[str]:
    for pattern in _DATE_RES:
        m = pattern.search(text)
        if not m:
            continue
        groups = m.groups()
        try:
            parsed = _parse_date_groups(groups)
            if parsed:
                return parsed.isoformat()
        except (ValueError, KeyError):
            continue
    return None


def _parse_date_groups(groups) -> Optional[date]:
    g = [str(x) for x in groups]

    # Pattern: YYYY-MM-DD
    if len(g[0]) == 4 and g[0].isdigit():
        return date(int(g[0]), int(g[1]), int(g[2]))

    # Pattern: DD-MM-YYYY or MM-DD-YYYY (ambiguous — assume DD/MM for non-US)
    if g[2].isdigit() and len(g[2]) in (2, 4):
        year = int(g[2]) + (2000 if len(g[2]) == 2 else 0)
        # Heuristic: if first group > 12, it must be day
        first, second = int(g[0]), int(g[1])
        if first > 12:
            return date(year, second, first)
        return date(year, first, second)

    # Pattern with month name
    for i, part in enumerate(g):
        month_num = _MONTH_MAP.get(part.lower())
        if month_num:
            others = [x for j, x in enumerate(g) if j != i and x.isdigit()]
            if len(others) == 2:
                nums = sorted([int(x) for x in others])
                year = nums[1] + (2000 if nums[1] < 100 else 0)
                day = nums[0]
                return date(year, month_num, day)
    return None


def _extract_amount(lines: list[str], full_text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Strategy:
      1. Look for a line containing a "total" keyword — take the amount from there.
      2. Fall back to the largest numeric value in the receipt (usually the total).
    """
    total_line = None
    for line in lines:
        if _TOTAL_KEYWORDS.search(line):
            total_line = line
            break

    search_text = total_line if total_line else full_text
    best_amount = None
    best_value = -1.0
    best_currency = None

    for m in _AMOUNT_RE.finditer(search_text):
        raw = m.group("amount").replace(",", "").replace(" ", "")
        try:
            val = float(raw)
        except ValueError:
            continue
        if val <= 0:
            continue

        # Currency detection priority: suffix > prefix_code > prefix_sym > Rs
        currency = (
            (m.group("suffix_code") or "").upper()
            or (m.group("prefix_code") or "").upper()
            or _SYM_TO_CODE.get(m.group("prefix_sym") or "")
            or ("INR" if "rs" in (search_text[:m.start()+5].lower()) else None)
        ) or None

        if val > best_value:
            best_value = val
            best_amount = f"{val:.2f}"
            best_currency = currency

    return best_amount, best_currency


def _extract_description(lines: list[str]) -> Optional[str]:
    """
    Collect item lines — those that look like "item name ... price".
    Take up to 5 items and join as a short description.
    """
    item_lines = []
    item_re = re.compile(r"^.{3,40}\s+\d+[\.,]\d{2}$")
    for line in lines:
        if item_re.match(line) and not _TOTAL_KEYWORDS.search(line):
            item_lines.append(line.strip())
        if len(item_lines) >= 5:
            break
    return "; ".join(item_lines) if item_lines else None


def _compute_confidence(result: OCRResult) -> float:
    score = 0.0
    if result.amount:      score += 0.4
    if result.date:        score += 0.3
    if result.merchant:    score += 0.2
    if result.description: score += 0.1
    return score