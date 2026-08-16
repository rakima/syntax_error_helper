import unittest

from syntax_helper import SyntaxAnalyzerService


class SyntaxAnalyzerServiceTest(unittest.TestCase):
    def test_exposes_supported_languages(self) -> None:
        self.assertEqual(("C", "Java", "Python", "JSON"), SyntaxAnalyzerService().languages)

    def test_rejects_unknown_language(self) -> None:
        with self.assertRaises(ValueError):
            SyntaxAnalyzerService().analyze("Ruby", "puts 'hello'")


if __name__ == "__main__":
    unittest.main()
