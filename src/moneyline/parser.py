"""Parsing of currency amount strings such as "$1,234.56" or "(42.00) USD".

This is a hand-written scanner rather than a regular expression so that
every failure can point at the exact character that broke expectations,
the way a compiler error does, instead of just saying "invalid format".
"""

from decimal import Decimal, InvalidOperation

from .amount import Money

SYMBOL_CURRENCY = {
    "$": "USD",
    "€": "EUR",  # €
    "£": "GBP",  # £
    "¥": "JPY",  # ¥
}


class ParseError(ValueError):
    """Raised when an amount string cannot be parsed.

    Carries the 1-based line and column of the offending character so
    callers can render a caret under it, the same way Python points at
    the source of a syntax error.
    """

    def __init__(self, reason: str, text: str, line: int, column: int):
        self.reason = reason
        self.text = text
        self.line = line
        self.column = column
        pointer = " " * (column - 1) + "^"
        super().__init__(
            f"{reason} at line {line}, column {column}\n"
            f"    {text}\n"
            f"    {pointer}"
        )


class _Scanner:
    """A read position into a single line of text."""

    def __init__(self, text: str, line: int):
        self.text = text
        self.line = line
        self.pos = 0

    def peek(self) -> str:
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def advance(self) -> str:
        ch = self.peek()
        self.pos += 1
        return ch

    def skip_spaces(self) -> None:
        while self.peek() == " ":
            self.pos += 1

    def fail(self, reason: str, at: int | None = None) -> ParseError:
        column = (self.pos if at is None else at) + 1
        return ParseError(reason, self.text, self.line, column)


def _try_trailing_symbol(scanner: _Scanner) -> str | None:
    """Consume a currency symbol at the scanner's current position, for
    layouts like "42.00$" or "1.234,56 €" where the symbol follows the
    number instead of leading it.
    """
    if scanner.peek() in SYMBOL_CURRENCY:
        currency = SYMBOL_CURRENCY[scanner.advance()]
        scanner.skip_spaces()
        return currency
    return None


def _validate_thousands_groups(
    scanner: _Scanner, groups: list[str], positions: list[int]
) -> None:
    if not groups[0] or len(groups[0]) > 3:
        raise scanner.fail("misplaced thousands separator", at=positions[0])
    for i, group in enumerate(groups[1:]):
        if len(group) != 3:
            raise scanner.fail("misplaced thousands separator", at=positions[i])


def _split_integer_and_fraction(
    scanner: _Scanner,
    digit_groups: list[str],
    sep_chars: list[str],
    sep_positions: list[int],
) -> tuple[str, str]:
    """Decide which separators are thousands grouping and which one, if
    any, is the decimal point, so both "1,234.56" and its locale-style
    mirror "1.234,56" parse to the same amount.
    """
    if not sep_chars:
        return digit_groups[0], ""

    if len(set(sep_chars)) == 2:
        # Both kinds of separator appear, so there's no ambiguity: the
        # last one is the decimal point, and everything before it must
        # consistently be the other character used for grouping.
        decimal_char = sep_chars[-1]
        decimal_pos = sep_positions[-1]
        thousands_char = "," if decimal_char == "." else "."
        for char, pos in zip(sep_chars[:-1], sep_positions[:-1]):
            if char != thousands_char:
                raise scanner.fail("misplaced decimal separator", at=pos)
        integer_groups = digit_groups[:-1]
        fraction = digit_groups[-1]
        _validate_thousands_groups(scanner, integer_groups, sep_positions[:-1])
        if not fraction:
            raise scanner.fail(
                "expected digits after decimal point", at=decimal_pos + 1
            )
        return "".join(integer_groups), fraction

    # Only one kind of separator appears. A repeated separator can only be
    # thousands grouping, since a number has at most one decimal point.
    if len(sep_chars) > 1:
        _validate_thousands_groups(scanner, digit_groups, sep_positions)
        return "".join(digit_groups), ""

    # Exactly one separator, with no locale to say what it means. A dot
    # is always treated as a decimal point, the same as before locale
    # support existed, so plain amounts like "19.99" are unaffected. A
    # comma is only grouping when it looks like one (exactly three
    # digits follow); otherwise it's read as a locale decimal point,
    # e.g. "42,50".
    second = digit_groups[1]
    if sep_chars[0] == "," and len(second) == 3:
        _validate_thousands_groups(scanner, digit_groups, sep_positions)
        return "".join(digit_groups), ""

    if not second:
        raise scanner.fail(
            "expected digits after decimal point", at=sep_positions[0] + 1
        )
    return digit_groups[0], second


def parse_amount(text: str, *, line: int = 1) -> Money:
    """Parse a single amount, such as "$1,234.56" or "(42.00) USD".

    `line` only affects how errors are labeled; callers reading many
    amounts from a file, one per line, pass the real line number so the
    error points at the right place in the file.
    """
    scanner = _Scanner(text, line)
    scanner.skip_spaces()

    if scanner.peek() == "":
        raise scanner.fail("empty amount")

    negative_parens = False
    if scanner.peek() == "(":
        negative_parens = True
        scanner.advance()
        scanner.skip_spaces()

    sign = -1 if negative_parens else 1

    if scanner.peek() in "+-":
        if scanner.peek() == "-":
            sign = -1
        scanner.advance()
        scanner.skip_spaces()

    currency = None
    if scanner.peek() in SYMBOL_CURRENCY:
        currency = SYMBOL_CURRENCY[scanner.advance()]
        scanner.skip_spaces()

    if scanner.peek() in "+-":
        if sign == -1 and scanner.peek() == "-":
            raise scanner.fail("duplicate sign")
        if scanner.peek() == "-":
            sign = -1
        scanner.advance()
        scanner.skip_spaces()

    if not scanner.peek().isdigit():
        raise scanner.fail("expected a digit")

    digit_groups = [""]
    sep_chars: list[str] = []
    sep_positions: list[int] = []
    while True:
        ch = scanner.peek()
        if ch in ".,":
            sep_chars.append(ch)
            sep_positions.append(scanner.pos)
            digit_groups.append("")
            scanner.advance()
        elif ch.isdigit():
            digit_groups[-1] += ch
            scanner.advance()
        else:
            break

    whole, fraction = _split_integer_and_fraction(
        scanner, digit_groups, sep_chars, sep_positions
    )

    scanner.skip_spaces()

    if currency is None:
        currency = _try_trailing_symbol(scanner)

    if negative_parens:
        if scanner.peek() != ")":
            raise scanner.fail("expected closing ')'")
        scanner.advance()
        scanner.skip_spaces()

    if currency is None:
        currency = _try_trailing_symbol(scanner)

    if currency is None and scanner.peek().isalpha():
        code_start = scanner.pos
        code = ""
        while scanner.peek().isalpha():
            code += scanner.advance()
        if len(code) != 3 or not code.isupper():
            raise scanner.fail(f"unrecognized currency code {code!r}", at=code_start)
        currency = code
        scanner.skip_spaces()

    if scanner.pos != len(scanner.text):
        raise scanner.fail("unexpected trailing text")

    try:
        amount = Decimal(f"{whole or '0'}.{fraction or '0'}")
    except InvalidOperation:
        raise scanner.fail("not a valid number") from None

    return Money(sign * amount, currency)
