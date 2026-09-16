# moneyline

Currency amounts show up as free text everywhere: CSV exports, invoices
pasted from email, config files, command-line arguments. Most of the
parsers I've reached for either accept a suspiciously wide range of
input silently (turning a typo into a wrong total) or reject it with a
message like `ValueError: invalid literal` that makes you go count
characters by hand to find the problem.

moneyline parses amount strings like `$1,234.56` or `(42.00) EUR` into
an exact `Money` value, and when the input is malformed it says exactly
where, with a line and column number and a caret, the same way a
compiler points at a syntax error.

No third-party dependencies — standard library only.

## Library usage

```python
from moneyline import parse_amount, Money, ParseError

a = parse_amount("$1,234.56")
b = parse_amount("25.00 USD")
print(a + b)  # 1,259.56 USD

try:
    parse_amount("12,34.56")
except ParseError as err:
    print(err)
```

That last block prints:

```
misplaced thousands separator at line 1, column 3
    12,34.56
      ^
```

The comma is in the wrong place — it should group digits in threes
counting from the decimal point — and the pointer lands on the exact
comma that's wrong, not just "somewhere in this string."

`Money` wraps a `decimal.Decimal`, not a `float`, so summing a column of
prices never drifts by a cent. Two amounts can only be added or
subtracted if their currencies match (or one of them has no currency
attached, e.g. a bare `42.00`).

Printing a `Money` respects its currency's minor unit: most currencies
show two decimal places, but a few, like the yen, show none.

```python
print(parse_amount("¥500"))       # 500 JPY, not 500.00 JPY
print(parse_amount("¥500.40"))    # printed as 500 JPY; the .40 is kept internally
print(parse_amount("¥500.40").rounded())  # 500 JPY, rounded away for good
```

`rounded()` quantizes the amount to its currency's minor unit (half-up),
returning a new `Money`; the unrounded value is left untouched until you
call it.

## Command-line usage

Parse one amount:

```
$ moneyline parse "(42.00) USD"
-42.00 USD
```

Sum a file with one amount per line, e.g. `amounts.txt`:

```
$10.00
$5,00.00
$25.50
```

```
$ moneyline sum amounts.txt
error: misplaced thousands separator at line 2, column 3
    $5,00.00
      ^
```

The sum command reports every bad line it finds (with its real line
number in the file) and exits non-zero without printing a total, rather
than silently adding up a subset of the file and calling it correct.
Fix line 2 and it prints the total:

```
$ moneyline sum amounts.txt
35.50
```

Without installing anything, the same commands work as:

```
$ python -m moneyline.cli parse "$1,234.56"
```

## What it currently understands

- Currency symbols, either leading or trailing: `$42.00`, `42.00$`, `1.234,56 €`
- Trailing ISO codes: `25.00 USD`
- A leading `-` or a trailing accounting-style `(...)` for negatives,
  with the symbol allowed on either side of the parentheses: `($42.00)`,
  `(42.00$)`, `(42.00) $`
- Thousands separators, validated for correct grouping: `1,234,567.89`
- Locale-style separators: `1.234,56` parses the same as `1,234.56`
- Currency-aware minor-unit precision for display and rounding (e.g.
  JPY has no minor unit, so `¥500` prints as `500 JPY`, not `500.00 JPY`)

When both `.` and `,` appear, the last one is the decimal point and the
other is grouping — that covers both `1,234.56` and its European mirror
`1.234,56` without guessing. When only one of them appears once, there's
no locale to consult: a `.` is always read as a decimal point (so plain
amounts like `19.99` are unaffected), and a `,` is read as grouping only
when it looks like one — exactly three digits after it, e.g. `1,234` —
otherwise it's a decimal point too, e.g. `42,50`.

Not yet supported (planned): a test suite covering parser edge cases
and error columns. See the issue tracker for the current shape of that
work.

## Installing

This is a plain `pyproject.toml` package with no dependencies:

```
pip install -e .
```

That gets you the `moneyline` command from the `[project.scripts]`
entry point; the library itself works with just the `src/` layout on
your `PYTHONPATH` if you'd rather not install it.
