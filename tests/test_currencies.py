import unittest

from moneyline.currencies import minor_units


class MinorUnitsTests(unittest.TestCase):
    def test_none_defaults_to_two(self):
        self.assertEqual(minor_units(None), 2)

    def test_common_currency_defaults_to_two(self):
        self.assertEqual(minor_units("USD"), 2)

    def test_unknown_code_defaults_to_two(self):
        self.assertEqual(minor_units("XYZ"), 2)

    def test_zero_decimal_currency(self):
        self.assertEqual(minor_units("JPY"), 0)

    def test_three_decimal_currency(self):
        self.assertEqual(minor_units("BHD"), 3)


if __name__ == "__main__":
    unittest.main()
