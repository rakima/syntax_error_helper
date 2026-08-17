import ast
import re

from syntax_helper.model import AnalysisResult, Severity
from syntax_helper.scanner import ScanConfig, structure_results

from .base import LanguageAnalyzer


BLOCK = re.compile(r"^\s*(if|elif|else|for|while|def|class|try|except|finally|with|match|case)\b")


class PythonAnalyzer(LanguageAnalyzer):
    language = "Python"
    config = ScanConfig(line_comments=("#",), triple_quotes=True)

    def analyze(self, source: str) -> list[AnalysisResult]:
        if not source.strip():
            return []
        results = structure_results(source, self.language, self.config)
        results.extend(self._simple_checks(source))
        try:
            ast.parse(source)
        except (SyntaxError, IndentationError) as error:
            results.append(self._from_syntax_error(source, error))
        return _deduplicate(results)

    def _simple_checks(self, source: str) -> list[AnalysisResult]:
        results = []
        for number, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if BLOCK.match(line) and not stripped.endswith((':', '\\')):
                results.append(AnalysisResult(
                    Severity.ERROR, self.language, number, number,
                    f"{number}行目の末尾に「:」が不足している可能性があります。",
                    "Pythonの制御文、関数、クラスなどはコロンで本体の開始を示します。",
                    stripped + ":",
                ))
            equal = re.search(r"\b(if|elif|while)\b(.+?)(?<![<>=!])=(?!=)", line)
            if equal:
                fixed = line[:equal.end() - 1] + "==" + line[equal.end():]
                results.append(AnalysisResult(
                    Severity.ERROR, self.language, number, number,
                    "条件式の「=」は「==」の書き間違いである可能性があります。",
                    "「=」は代入に使用します。値の比較には通常「==」を使用します。",
                    fixed.strip(),
                ))
        return results

    def _from_syntax_error(self, source: str, error: SyntaxError) -> AnalysisResult:
        lines = source.splitlines() or [""]
        line_no = max(1, min(error.lineno or 1, len(lines)))
        suspected = line_no
        message = f"{line_no}行目付近のPython構文を確認してください。"
        reason = "Pythonの構文解析器がコードを読み取れませんでした。"
        suggestion = f"{line_no}行目と、その直前の行を確認してください。"
        lower = (error.msg or "").lower()

        if isinstance(error, IndentationError) or "indent" in lower:
            message = f"{line_no}行目のインデントが周囲と一致しない可能性があります。"
            reason = "Pythonでは字下げによって処理のまとまりを表します。"
            suggestion = "同じブロックの行でスペース数をそろえ、タブとスペースの混在を確認してください。"
        elif "expected ':'" in lower:
            message = f"{line_no}行目の末尾に「:」が不足している可能性があります。"
            reason = "ブロックを開始する文の末尾にはコロンが必要です。"
            suggestion = lines[line_no - 1].rstrip() + ":"
        elif line_no > 1 and BLOCK.match(lines[line_no - 2]) and not lines[line_no - 2].rstrip().endswith(":"):
            suspected = line_no - 1
            message = f"{suspected}行目の末尾に「:」が不足している可能性があります。"
            reason = "次の行を読み始めた位置でエラーになりましたが、直前のブロック開始文が原因の可能性があります。"
            suggestion = lines[suspected - 1].rstrip() + ":"
        return AnalysisResult(Severity.ERROR, self.language, line_no, suspected, message, reason, suggestion)


def _deduplicate(results: list[AnalysisResult]) -> list[AnalysisResult]:
    seen = set()
    unique = []
    for result in results:
        key = (result.suspected_line, result.message)
        if key not in seen:
            seen.add(key)
            unique.append(result)
    return unique
