"""The core value type: an exact amount paired with an optional currency."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from .currencies import minor_units


@dataclass(frozen=True)
class Money:
    """An amount of money.

    Stored as a Decimal rather than a float so that combining amounts
    never drifts (0.10 + 0.20 is exactly 0.30 here, unlike with binary
    floats). Currency is optional: a bare number with no symbol or code
    parses fine, and such an amount can be combined with anything.
    """

    amount: Decimal
    currency: str | None = None

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount + other.amount, self._merged_currency(other))

    def __sub__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount - other.amount, self._merged_currency(other))

    def __neg__(self) -> "Money":
        return Money(-self.amount, self.currency)

    def _merged_currency(self, other: "Money") -> str | None:
        if self.currency and other.currency and self.currency != other.currency:
            raise ValueError(
                f"cannot combine {self.currency} and {other.currency} amounts"
            )
        return self.currency or other.currency

    def rounded(self) -> "Money":
        """Round to this amount's currency's minor-unit precision, e.g.
        to whole yen for JPY. Amounts with no attached currency round
        to 2 places, the general-purpose default.
        """
        digits = minor_units(self.currency)
        quantum = Decimal(1).scaleb(-digits)
        return Money(self.amount.quantize(quantum, rounding=ROUND_HALF_UP), self.currency)

    def __str__(self) -> str:
        text = f"{self.amount:,.{minor_units(self.currency)}f}"
        return f"{text} {self.currency}" if self.currency else text
