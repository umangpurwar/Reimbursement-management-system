from __future__ import annotations
from django.conf import settings
import logging
import time
from functools import lru_cache
from typing import Optional

import requests

logger = logging.getLogger(__name__)

BASE_CURRENCY = "INR"
_RATES_TTL_SECONDS = 3600        # re-fetch rates every hour
_COUNTRIES_TTL_SECONDS = 86400   # re-fetch country/currency list once a day

_rates_cache: dict[str, float] = {}
_rates_fetched_at: float = 0.0

_currencies_cache: list[dict] = []
_currencies_fetched_at: float = 0.0


 
# Public API
 

def convert_to_inr(amount: float, from_currency: str) -> tuple[float, float]:
    from_currency = from_currency.upper().strip()

    if from_currency == BASE_CURRENCY:
        return round(amount, 2), 1.0

    rates = _get_rates()

    if from_currency not in rates:
        raise CurrencyError(
            f"Exchange rate for '{from_currency}' not available. "
            f"Supported codes: {', '.join(sorted(rates.keys())[:20])}..."
        )

    rate = rates[from_currency]
    inr_amount = round(amount * rate, 2)
    return inr_amount, round(rate, 6)


def get_supported_currencies() -> list[dict]:
    """
    Returns a list of dicts:
        [{ "code": "USD", "name": "US Dollar", "symbol": "$" }, ...]

    Built from restcountries.com — enriched with the live rate list
    so only currencies with available rates are returned.
    """
    country_currencies = _get_country_currencies()
    available_codes = set(_get_rates().keys()) | {BASE_CURRENCY}

    result = []
    seen = set()
    for entry in country_currencies:
        code = entry.get("code", "")
        if code and code not in seen and code in available_codes:
            result.append(entry)
            seen.add(code)

    result.sort(key=lambda x: x["code"])
    return result


class CurrencyError(Exception):
    """Raised when a currency code is not supported or fetch fails."""


 
# Internal — exchange rates


def _get_rates() -> dict[str, float]:
    global _rates_cache, _rates_fetched_at

    if _rates_cache and (time.time() - _rates_fetched_at) < _RATES_TTL_SECONDS:
        return _rates_cache

    url = f"{settings.EXCHANGE_RATE_API}/{BASE_CURRENCY}"
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error("Failed to fetch exchange rates: %s", e)
        if _rates_cache:
            logger.warning("Using stale exchange rate cache.")
            return _rates_cache
        raise CurrencyError(f"Exchange rate service unavailable: {e}") from e

    # API returns "1 INR = X foreign", we want "1 foreign = Y INR"
    raw_rates = data.get("rates", {})
    _rates_cache = {
        code: round(1 / rate, 6)
        for code, rate in raw_rates.items()
        if rate and rate > 0 and code != BASE_CURRENCY
    }
    _rates_cache[BASE_CURRENCY] = 1.0
    _rates_fetched_at = time.time()

    logger.info("Exchange rates refreshed. %d currencies loaded.", len(_rates_cache))
    return _rates_cache



# Internal — country/currency metadata


def _get_country_currencies() -> list[dict]:
    global _currencies_cache, _currencies_fetched_at

    if _currencies_cache and (time.time() - _currencies_fetched_at) < _COUNTRIES_TTL_SECONDS:
        return _currencies_cache

    url = settings.COUNTRIES_API
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        countries = resp.json()
    except requests.RequestException as e:
        logger.error("Failed to fetch country/currency list: %s", e)
        return _currencies_cache or []

    entries = []
    for country in countries:
        currencies = country.get("currencies", {})
        for code, info in currencies.items():
            entries.append({
                "code":   code.upper(),
                "name":   info.get("name", code),
                "symbol": info.get("symbol", ""),
            })

    _currencies_cache = entries
    _currencies_fetched_at = time.time()
    logger.info("Country currencies refreshed. %d entries loaded.", len(entries))
    return _currencies_cache