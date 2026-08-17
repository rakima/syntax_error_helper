from pathlib import Path
import unittest

from syntax_helper import SyntaxAnalyzerService


ROOT = Path(__file__).resolve().parents[1]


class ExampleFilesTest(unittest.TestCase):
    cases = (
        ("C", "examples/c/valid.c", "examples/c/syntax_errors.c"),
        ("Java", "examples/java/ValidSample.java", "examples/java/SyntaxErrors.java"),
        ("Python", "examples/python/valid.py", "examples/python/syntax_errors.py"),
        ("JSON", "examples/json/valid.json", "examples/json/syntax_errors.json"),
    )

    def setUp(self) -> None:
        self.service = SyntaxAnalyzerService()

    def test_valid_examples_have_no_candidates(self) -> None:
        for language, valid_path, _ in self.cases:
            with self.subTest(language=language):
                source = (ROOT / valid_path).read_text(encoding="utf-8")
                self.assertEqual([], self.service.analyze(language, source))

    def test_error_examples_have_candidates(self) -> None:
        for language, _, error_path in self.cases:
            with self.subTest(language=language):
                source = (ROOT / error_path).read_text(encoding="utf-8")
                self.assertGreaterEqual(len(self.service.analyze(language, source)), 2)


if __name__ == "__main__":
    unittest.main()
