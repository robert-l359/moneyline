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

    whole = ""
    current_group = 0
    group_sizes = []
    comma_positions = []
    while True:
        ch = scanner.peek()
        if ch == ",":
            comma_positions.append(scanner.pos)
            group_sizes.append(current_group)
            current_group = 0
            scanner.advance()
        elif ch.isdigit():
            whole += ch
            current_group += 1
            scanner.advance()
        else:
            break
    group_sizes.append(current_group)

    if len(group_sizes) > 1:
        if group_sizes[0] == 0 or group_sizes[0] > 3:
            raise scanner.fail("misplaced thousands separator", at=comma_positions[0])
        for i, size in enumerate(group_sizes[1:]):
            if size != 3:
                raise scanner.fail(
                    "misplaced thousands separator", at=comma_positions[i]
                )

    fraction = ""
    if scanner.peek() == ".":
        scanner.advance()
        frac_start = scanner.pos
        while scanner.peek().isdigit():
            fraction += scanner.advance()
        if not fraction:
            raise scanner.fail("expected digits after decimal point", at=frac_start)

    scanner.skip_spaces()

    if negative_parens:
        if scanner.peek() != ")":
            raise scanner.fail("expected closing ')'")
        scanner.advance()
        scanner.skip_spaces()

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
