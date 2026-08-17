import unittest

from syntax_helper.analyzers import JsonAnalyzer


class JsonAnalyzerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = JsonAnalyzer()

    def test_valid_json_has_no_results(self) -> None:
        self.assertEqual([], self.analyzer.analyze('{"items": [1, {"ok": true}]}'))

    def test_missing_comma_suspects_previous_line(self) -> None:
        results = self.analyzer.analyze('{\n  "name": "A"\n  "age": 10\n}')
        candidate = next(result for result in results if "不足" in result.message)
        self.assertEqual((3, 2), (candidate.error_line, candidate.suspected_line))

    def test_unquoted_key(self) -> None:
        results = self.analyzer.analyze('{name: "A"}')
        self.assertTrue(any("ダブルクォート" in result.message for result in results))

    def test_trailing_comma(self) -> None:
        results = self.analyzer.analyze('{\n  "name": "A",\n}')
        self.assertTrue(any("余分" in result.message for result in results))


if __name__ == "__main__":
    unittest.main()
