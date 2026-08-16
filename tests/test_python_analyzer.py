import unittest

from syntax_helper.analyzers import PythonAnalyzer


class PythonAnalyzerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = PythonAnalyzer()

    def test_valid_python_has_no_results(self) -> None:
        source = "if value == 10:\n    print(\"ok\")\n"
        self.assertEqual([], self.analyzer.analyze(source))

    def test_single_equal_suggests_double_equal(self) -> None:
        results = self.analyzer.analyze("if x = 10:\n    print(x)\n")
        candidate = next(result for result in results if "==" in result.message)
        self.assertIn("if x == 10:", candidate.suggestion)

    def test_missing_colon(self) -> None:
        results = self.analyzer.analyze("if True\n    print('yes')")
        self.assertTrue(any(":」が不足" in result.message for result in results))

    def test_indentation_error(self) -> None:
        results = self.analyzer.analyze("if True:\nprint('yes')")
        self.assertTrue(any("インデント" in result.message for result in results))

    def test_brackets_in_string_and_comment_are_ignored(self) -> None:
        source = 'value = "]"\n# ( {\nprint(value)\n'
        self.assertEqual([], self.analyzer.analyze(source))


if __name__ == "__main__":
    unittest.main()
