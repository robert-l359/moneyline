import unittest
from decimal import Decimal

from moneyline import Money


class ArithmeticTests(unittest.TestCase):
    def test_add_same_currency(self):
        total = Money(Decimal("1.10"), "USD") + Money(Decimal("2.20"), "USD")
        self.assertEqual(total, Money(Decimal("3.30"), "USD"))

    def test_add_never_drifts_like_float_would(self):
        total = Money(Decimal("0.10"), None) + Money(Decimal("0.20"), None)
        self.assertEqual(total.amount, Decimal("0.30"))

    def test_sub_same_currency(self):
        result = Money(Decimal("5.00"), "EUR") - Money(Decimal("2.00"), "EUR")
        self.assertEqual(result, Money(Decimal("3.00"), "EUR"))

    def test_neg(self):
        self.assertEqual(-Money(Decimal("5.00"), "USD"), Money(Decimal("-5.00"), "USD"))

    def test_bare_amount_takes_on_the_other_side_currency(self):
        total = Money(Decimal("10.00"), None) + Money(Decimal("5.00"), "USD")
        self.assertEqual(total, Money(Decimal("15.00"), "USD"))

    def test_two_bare_amounts_stay_bare(self):
        total = Money(Decimal("10.00"), None) + Money(Decimal("5.00"), None)
        self.assertIsNone(total.currency)

    def test_mismatched_currencies_cannot_combine(self):
        with self.assertRaises(ValueError):
            Money(Decimal("10.00"), "USD") + Money(Decimal("10.00"), "EUR")

    def test_add_rejects_non_money(self):
        with self.assertRaises(TypeError):
            Money(Decimal("1.00"), "USD") + 1


class RoundedTests(unittest.TestCase):
    def test_default_rounds_to_two_places(self):
        rounded = Money(Decimal("1.005"), None).rounded()
        self.assertEqual(rounded.amount, Decimal("1.01"))

    def test_jpy_has_no_minor_unit(self):
        rounded = Money(Decimal("500.40"), "JPY").rounded()
        self.assertEqual(rounded.amount, Decimal("500"))

    def test_bhd_rounds_to_three_places(self):
        rounded = Money(Decimal("1.2345"), "BHD").rounded()
        self.assertEqual(rounded.amount, Decimal("1.235"))

    def test_rounded_leaves_original_untouched(self):
        original = Money(Decimal("500.40"), "JPY")
        original.rounded()
        self.assertEqual(original.amount, Decimal("500.40"))


class StrTests(unittest.TestCase):
    def test_with_currency(self):
        self.assertEqual(str(Money(Decimal("1234.5"), "USD")), "1,234.50 USD")

    def test_without_currency(self):
        self.assertEqual(str(Money(Decimal("42"), None)), "42.00")

    def test_jpy_prints_without_decimals(self):
        self.assertEqual(str(Money(Decimal("500"), "JPY")), "500 JPY")


if __name__ == "__main__":
    unittest.main()
