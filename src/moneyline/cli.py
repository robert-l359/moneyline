"""The `moneyline` command: parse one amount, or sum a file of them."""

import argparse
import sys

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

    sum_cmd = sub.add_parser("sum", help="sum one amount per line from a file")
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
    total = None
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
            total = money if total is None else total + money

    if had_error:
        return 1
    print(total if total is not None else "0.00")
    return 0


if __name__ == "__main__":
    sys.exit(main())
