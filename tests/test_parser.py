import unittest
from decimal import Decimal

from moneyline import Money, ParseError, parse_amount


class LeadingSymbolTests(unittest.TestCase):
    def test_dollar(self):
        money = parse_amount("$1,234.56")
        self.assertEqual(money, Money(Decimal("1234.56"), "USD"))

    def test_euro(self):
        money = parse_amount("€42.00")
        self.assertEqual(money, Money(Decimal("42.00"), "EUR"))

    def test_symbol_then_space(self):
        money = parse_amount("$ 42.00")
        self.assertEqual(money, Money(Decimal("42.00"), "USD"))

    def test_bare_number_has_no_currency(self):
        money = parse_amount("42.00")
        self.assertIsNone(money.currency)


class TrailingSymbolAndCodeTests(unittest.TestCase):
    def test_trailing_symbol(self):
        money = parse_amount("42.00$")
        self.assertEqual(money, Money(Decimal("42.00"), "USD"))

    def test_trailing_symbol_with_space(self):
        money = parse_amount("1.234,56 €")
        self.assertEqual(money, Money(Decimal("1234.56"), "EUR"))

    def test_trailing_iso_code(self):
        money = parse_amount("25.00 USD")
        self.assertEqual(money, Money(Decimal("25.00"), "USD"))

    def test_unrecognized_code_must_be_three_uppercase_letters(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("42.00 usd")
        self.assertIn("unrecognized currency code 'usd'", str(ctx.exception))

    def test_code_wrong_length(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("42.00 US")
        self.assertIn("unrecognized currency code 'US'", str(ctx.exception))


class NegativeTests(unittest.TestCase):
    def test_leading_minus(self):
        money = parse_amount("-42.00")
        self.assertEqual(money, Money(Decimal("-42.00"), None))

    def test_leading_plus(self):
        money = parse_amount("+42.00")
        self.assertEqual(money, Money(Decimal("42.00"), None))

    def test_accounting_parens(self):
        money = parse_amount("(42.00)")
        self.assertEqual(money, Money(Decimal("-42.00"), None))

    def test_parens_with_symbol_inside(self):
        money = parse_amount("($42.00)")
        self.assertEqual(money, Money(Decimal("-42.00"), "USD"))

    def test_parens_with_symbol_before_closing_paren(self):
        money = parse_amount("(42.00$)")
        self.assertEqual(money, Money(Decimal("-42.00"), "USD"))

    def test_parens_with_symbol_after_closing_paren(self):
        money = parse_amount("(42.00) $")
        self.assertEqual(money, Money(Decimal("-42.00"), "USD"))

    def test_minus_after_symbol(self):
        money = parse_amount("$-42.00")
        self.assertEqual(money, Money(Decimal("-42.00"), "USD"))

    def test_duplicate_sign_is_an_error(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("-$-42.00")
        self.assertIn("duplicate sign", str(ctx.exception))


class ThousandsSeparatorTests(unittest.TestCase):
    def test_single_group(self):
        money = parse_amount("1,234.56")
        self.assertEqual(money.amount, Decimal("1234.56"))

    def test_multiple_groups(self):
        money = parse_amount("1,234,567.89")
        self.assertEqual(money.amount, Decimal("1234567.89"))

    def test_first_group_may_be_short(self):
        money = parse_amount("12,345.00")
        self.assertEqual(money.amount, Decimal("12345.00"))

    def test_misplaced_separator_reports_its_own_column(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("12,34.56")
        err = ctx.exception
        self.assertIn("misplaced thousands separator", str(err))
        self.assertEqual(err.column, 3)

    def test_misplaced_separator_in_later_group(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("1,234,56.00")
        err = ctx.exception
        self.assertEqual(err.column, 6)

    def test_leading_separator_is_an_error(self):
        with self.assertRaises(ParseError):
            parse_amount(",234.00")


class LocaleSeparatorTests(unittest.TestCase):
    def test_dot_grouping_comma_decimal(self):
        money = parse_amount("1.234,56")
        self.assertEqual(money.amount, Decimal("1234.56"))

    def test_mismatched_grouping_char_is_an_error(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("1,234.567,89")
        self.assertIn("misplaced decimal separator", str(ctx.exception))

    def test_lone_comma_three_digits_is_grouping(self):
        money = parse_amount("1,234")
        self.assertEqual(money.amount, Decimal("1234"))

    def test_lone_comma_two_digits_is_decimal(self):
        money = parse_amount("42,50")
        self.assertEqual(money.amount, Decimal("42.50"))

    def test_lone_dot_is_always_decimal(self):
        money = parse_amount("19.99")
        self.assertEqual(money.amount, Decimal("19.99"))

    def test_trailing_decimal_point_needs_digits(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("42.")
        self.assertIn("expected digits after decimal point", str(ctx.exception))


class ErrorReportingTests(unittest.TestCase):
    def test_empty_amount(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("")
        err = ctx.exception
        self.assertEqual(err.column, 1)
        self.assertIn("empty amount", str(err))

    def test_blank_amount(self):
        with self.assertRaises(ParseError):
            parse_amount("   ")

    def test_expected_a_digit(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("$abc")
        err = ctx.exception
        self.assertIn("expected a digit", str(err))
        self.assertEqual(err.column, 2)

    def test_unclosed_parens(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("(42.00")
        self.assertIn("expected closing ')'", str(ctx.exception))

    def test_trailing_garbage(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("42.00 USD extra")
        err = ctx.exception
        self.assertIn("unexpected trailing text", str(err))
        self.assertEqual(err.column, 11)

    def test_error_message_caret_aligns_with_offending_character(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("12,34.56")
        err = ctx.exception
        source_line, pointer_line = str(err).splitlines()[-2:]
        caret_index = pointer_line.index("^")
        self.assertEqual(source_line[caret_index], ",")
        self.assertEqual(err.column, 3)

    def test_custom_line_number_is_reported(self):
        with self.assertRaises(ParseError) as ctx:
            parse_amount("12,34.56", line=7)
        self.assertIn("line 7", str(ctx.exception))
        self.assertEqual(ctx.exception.line, 7)


if __name__ == "__main__":
    unittest.main()
