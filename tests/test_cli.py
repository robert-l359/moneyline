import contextlib
import io
import os
import tempfile
import unittest

from moneyline.cli import main


class ParseCommandTests(unittest.TestCase):
    def test_prints_normalized_amount(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["parse", "(42.00) USD"])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().strip(), "-42.00 USD")

    def test_bad_amount_prints_error_and_exits_nonzero(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = main(["parse", "12,34.56"])
        self.assertEqual(code, 1)
        self.assertIn("misplaced thousands separator", err.getvalue())


class SumCommandTests(unittest.TestCase):
    def _write(self, lines: list[str]) -> str:
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        try:
            handle.write("\n".join(lines) + "\n")
        finally:
            handle.close()
        self.addCleanup(os.remove, handle.name)
        return handle.name

    def test_sums_valid_file(self):
        path = self._write(["$10.00", "$5.00", "", "$25.50"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["sum", path])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().strip(), "40.50 USD")

    def test_reports_every_bad_line_and_prints_no_total(self):
        path = self._write(["$10.00", "$5,00.00", "$25.50"])
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["sum", path])
        self.assertEqual(code, 1)
        self.assertIn("line 2", err.getvalue())
        self.assertEqual(out.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
