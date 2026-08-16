import unittest

from syntax_helper.analyzers import CAnalyzer, JavaAnalyzer


class CAnalyzerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = CAnalyzer()

    def test_valid_control_statements_are_not_semicolon_errors(self) -> None:
        source = "int main(void) {\n  if (1) {\n    return 0;\n  }\n}"
        self.assertEqual([], self.analyzer.analyze(source))

    def test_missing_semicolon_suspects_previous_line(self) -> None:
        results = self.analyzer.analyze('int a = 10\nprintf("%d\\n", a);')
        candidate = next(result for result in results if "セミコロン" in result.reason)
        self.assertEqual((2, 1), (candidate.error_line, candidate.suspected_line))

    def test_uninitialized_declaration_can_be_detected(self) -> None:
        results = self.analyzer.analyze("int count\nprintf(\"ok\");")
        self.assertTrue(any(result.suspected_line == 1 for result in results))

    def test_for_requires_two_semicolons(self) -> None:
        results = self.analyzer.analyze("for (int i = 0 i < 3; i++) {\n}")
        self.assertTrue(any("for 文" in result.message for result in results))

    def test_comment_brackets_are_ignored(self) -> None:
        self.assertEqual([], self.analyzer.analyze("int x = 1; // }])"))


class JavaAnalyzerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = JavaAnalyzer()

    def test_valid_java_has_no_results(self) -> None:
        source = "class A {\n  void run() {\n    System.out.println(1);\n  }\n}"
        self.assertEqual([], self.analyzer.analyze(source))

    def test_unclosed_class_body_points_to_opening_line(self) -> None:
        source = "class A {\n  void run() {\n    System.out.println(1);\n  }"
        results = self.analyzer.analyze(source)
        candidate = next(result for result in results if "閉じられていない" in result.message)
        self.assertEqual(1, candidate.suspected_line)


if __name__ == "__main__":
    unittest.main()
