import unittest

from syntax_helper.model import AnalysisResult, Severity


class AnalysisResultTest(unittest.TestCase):
    def setUp(self) -> None:
        self.result = AnalysisResult(
            severity=Severity.ERROR,
            language="C",
            error_line=2,
            suspected_line=1,
            message="セミコロンが不足している可能性があります。",
            reason="次の行でエラーになることがあります。",
            suggestion="int value = 10;",
        )

    def test_analysis_and_suggestion_are_separate_sections(self) -> None:
        self.assertIn("原因候補は1行目です。", self.result.analysis_text())
        self.assertIn("理由:", self.result.analysis_text())
        self.assertNotIn("修正候補:", self.result.analysis_text())
        self.assertEqual("修正候補:\nint value = 10;", self.result.suggestion_text())

    def test_combined_text_keeps_existing_format(self) -> None:
        self.assertEqual(
            f"{self.result.analysis_text()}\n\n{self.result.suggestion_text()}",
            self.result.to_japanese_text(),
        )


if __name__ == "__main__":
    unittest.main()
