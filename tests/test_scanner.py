import unittest

from syntax_helper.scanner import ScanConfig, scan_structure


class StructureScannerTest(unittest.TestCase):
    config = ScanConfig(line_comments=("//",), block_comments=(("/*", "*/"),))

    def test_ignores_brackets_in_comments_and_strings(self) -> None:
        source = 'printf("( [ }"); // {\n/* ( */\nint values[2] = {1, 2};'
        self.assertEqual([], scan_structure(source, self.config))

    def test_reports_original_line_for_nested_unclosed_brackets(self) -> None:
        issues = scan_structure("if (ok) {\n  call(values[0]);", self.config)
        self.assertEqual(1, len(issues))
        self.assertEqual(("{", 1, "}"), (issues[0].symbol, issues[0].related_line, issues[0].expected))

    def test_reports_multiple_candidates(self) -> None:
        issues = scan_structure("call(\narray[0;", self.config)
        self.assertEqual({"(", "["}, {issue.symbol for issue in issues})

    def test_reports_unclosed_block_comment(self) -> None:
        issues = scan_structure("int x; /* comment", self.config)
        self.assertEqual("unclosed_comment", issues[0].kind)


if __name__ == "__main__":
    unittest.main()
