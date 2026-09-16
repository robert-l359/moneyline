"""Per-currency minor-unit precision.

Most currencies quote to two decimal digits (cents, pence, ...), but
that isn't universal: yen and a handful of others have no minor unit
at all, and a few Gulf currencies use three digits instead of two.
Formatting or rounding every currency to two places regardless would
silently turn "¥500" into "¥500.00", which isn't just cosmetically odd
-- it invents precision the amount never had.
"""

DEFAULT_MINOR_UNITS = 2

# ISO 4217 minor-unit digit counts, limited to currencies that differ
# from the default of 2.
_MINOR_UNIT_OVERRIDES = {
    "JPY": 0,
    "KRW": 0,
    "VND": 0,
    "CLP": 0,
    "ISK": 0,
    "BHD": 3,
    "JOD": 3,
    "KWD": 3,
    "OMR": 3,
    "TND": 3,
}


def minor_units(currency: str | None) -> int:
    """Number of digits after the decimal point `currency` is normally
    quoted to. Unknown or missing currencies default to 2.
    """
    if currency is None:
        return DEFAULT_MINOR_UNITS
    return _MINOR_UNIT_OVERRIDES.get(currency, DEFAULT_MINOR_UNITS)
