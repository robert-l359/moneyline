"""The `moneyline` command: parse one amount, or sum a file of them."""

import argparse
import sys

from .amount import Money
from .parser import ParseError, parse_amount


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="moneyline", description="parse and total currency amounts"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    parse_cmd = sub.add_parser(
        "parse", help="parse a single amount and print its normalized form"
    )
    parse_cmd.add_argument("amount", help='e.g. "$1,234.56" or "(42.00) EUR"')

    sum_cmd = sub.add_parser(
        "sum", help="sum one amount per line from a file, grouped by currency"
    )
    sum_cmd.add_argument("path", help="file with one amount per line")

    args = parser.parse_args(argv)

    if args.command == "parse":
        return _parse_one(args.amount)
    return _sum_file(args.path)


def _parse_one(text: str) -> int:
    try:
        money = parse_amount(text)
    except ParseError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(money)
    return 0


def _sum_file(path: str) -> int:
    # Money.__add__ refuses to combine two different currencies, so a file
    # mixing e.g. USD and EUR lines can't be reduced to one running total.
    # Keep a separate running total per currency instead of picking one
    # arbitrarily or erroring out on a file that's legitimately multi-currency.
    totals: dict[str | None, Money] = {}
    had_error = False
    with open(path, encoding="utf-8") as handle:
        for lineno, raw_line in enumerate(handle, start=1):
            text = raw_line.rstrip("\n")
            if not text.strip():
                continue
            try:
                money = parse_amount(text, line=lineno)
            except ParseError as err:
                print(f"error: {err}", file=sys.stderr)
                had_error = True
                continue
            existing = totals.get(money.currency)
            totals[money.currency] = money if existing is None else existing + money

    if had_error:
        return 1
    if not totals:
        print("0.00")
        return 0
    for currency in sorted(totals, key=lambda c: c or ""):
        print(totals[currency])
    return 0


if __name__ == "__main__":
    sys.exit(main())
