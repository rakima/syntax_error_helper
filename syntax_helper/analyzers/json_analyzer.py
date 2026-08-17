import json
import re

from syntax_helper.model import AnalysisResult, Severity
from syntax_helper.scanner import ScanConfig, structure_results

from .base import LanguageAnalyzer


class JsonAnalyzer(LanguageAnalyzer):
    language = "JSON"
    config = ScanConfig(quote_chars=('"',))

    def analyze(self, source: str) -> list[AnalysisResult]:
        structural = structure_results(source, self.language, self.config)
        if not source.strip():
            return []
        try:
            json.loads(source)
            return structural
        except json.JSONDecodeError as error:
            inferred = self._infer(source, error)
            return _deduplicate(structural + [inferred])

    def _infer(self, source: str, error: json.JSONDecodeError) -> AnalysisResult:
        lines = source.splitlines() or [""]
        line_no = max(1, min(error.lineno, len(lines)))
        line = lines[line_no - 1]
        previous_no = max(1, line_no - 1)
        previous = lines[previous_no - 1].rstrip()
        message = "JSONの書き方を確認してください。"
        reason = "JSONパーサーが値や区切りを正しく読み取れませんでした。"
        suggestion = f"{line_no}行目付近の引用符、コロン、カンマを確認してください。"
        suspected = line_no

        key_match = re.match(r"(\s*[{,]?\s*)([A-Za-z_$][\w$-]*)(\s*:)", line)
        if key_match:
            message = "JSONのキーがダブルクォートで囲まれていない可能性があります。"
            reason = "JSONではオブジェクトのキーをダブルクォートで囲む必要があります。"
            suggestion = (
                line[:key_match.start(2)] + f'"{key_match.group(2)}"' + line[key_match.end(2):]
            ).strip()
        elif error.msg == "Expecting ':' delimiter":
            message = "キーと値の間に「:」が不足している可能性があります。"
            reason = "JSONではキーの後をコロンで区切ります。"
            suggestion = f"{line_no}行目のキーの後に「:」を追加してください。"
        elif "trailing comma" in error.msg.lower():
            suspected = line_no
            message = f"{line_no}行目末尾の「,」が余分な可能性があります。"
            reason = "JSONでは最後の要素の後にカンマを置けません。"
            suggestion = line[:error.colno - 1].rstrip() + line[error.colno:]
        elif error.msg in {"Expecting ',' delimiter", "Expecting property name enclosed in double quotes"}:
            if previous_no < line_no and previous and not previous.endswith((",", "{", "[")):
                suspected = previous_no
                message = f"{previous_no}行目の末尾に「,」が不足している可能性があります。"
                reason = "次の要素との区切りをパーサーが見つけられませんでした。"
                suggestion = previous + ","
            elif re.match(r"\s*[}\]]", line) and previous.endswith(","):
                suspected = previous_no
                message = f"{previous_no}行目末尾の「,」が余分な可能性があります。"
                reason = "JSONでは最後の要素の後にカンマを置けません。"
                suggestion = previous[:-1]
        elif error.msg == "Extra data":
            message = "JSONの値の後に余分な内容がある可能性があります。"
            reason = "1つ目のJSON値を読み終えた後にも文字が見つかりました。"
            suggestion = f"{line_no}行目付近の余分な値または区切りを確認してください。"

        return AnalysisResult(Severity.ERROR, self.language, line_no, suspected, message, reason, suggestion)


def _deduplicate(results: list[AnalysisResult]) -> list[AnalysisResult]:
    seen: set[tuple[int, int, str]] = set()
    unique = []
    for result in results:
        key = (result.error_line, result.suspected_line, result.message)
        if key not in seen:
            seen.add(key)
            unique.append(result)
    return unique
