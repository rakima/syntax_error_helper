import re

from syntax_helper.model import AnalysisResult, Severity
from syntax_helper.scanner import ScanConfig, structure_results

from .base import LanguageAnalyzer


CONTROL = re.compile(r"^\s*(if|for|while|switch|catch|synchronized)\b")
NON_STATEMENT_ENDINGS = (";", "{", "}", ":", ",", "\\")


class CLikeAnalyzer(LanguageAnalyzer):
    config = ScanConfig(line_comments=("//",), block_comments=(("/*", "*/"),))

    def analyze(self, source: str) -> list[AnalysisResult]:
        results = structure_results(source, self.language, self.config)
        sanitized = _sanitize_lines(source)
        results.extend(self._control_checks(sanitized))
        results.extend(self._semicolon_checks(sanitized))
        return _deduplicate(results)

    def _control_checks(self, lines: list[str]) -> list[AnalysisResult]:
        results: list[AnalysisResult] = []
        for number, line in enumerate(lines, 1):
            match = CONTROL.match(line)
            if not match:
                continue
            keyword = match.group(1)
            open_at = line.find("(", match.end())
            close_at = line.rfind(")")
            if open_at < 0 or close_at < open_at:
                results.append(AnalysisResult(
                    Severity.ERROR, self.language, number, number,
                    f"{keyword} の条件を閉じる「)」が不足している可能性があります。",
                    f"{keyword} の条件は「(」と「)」で囲む必要があります。",
                    f"{number}行目の条件の後に「)」を追加できるか確認してください。",
                ))
            if keyword == "for" and open_at >= 0 and close_at > open_at:
                body = line[open_at + 1:close_at]
                if body.count(";") != 2 and ":" not in body:
                    results.append(AnalysisResult(
                        Severity.ERROR, self.language, number, number,
                        "for 文の「;」が不足している可能性があります。",
                        "通常の for 文では初期化・条件・更新を2つのセミコロンで区切ります。",
                        f"{number}行目の for 文内に「;」が2つあるか確認してください。",
                    ))
        return results

    def _semicolon_checks(self, lines: list[str]) -> list[AnalysisResult]:
        results: list[AnalysisResult] = []
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not _looks_like_statement(stripped):
                continue
            next_line = next((item.strip() for item in lines[index + 1:] if item.strip()), "")
            if not next_line and stripped.endswith(")") and CONTROL.match(stripped):
                continue
            number = index + 1
            results.append(AnalysisResult(
                Severity.ERROR, self.language, min(number + 1, len(lines)), number,
                f"{number}行目の末尾に「;」が不足している可能性があります。",
                "文の終わりを示すセミコロンが見つかりません。次の行でエラーになることがあります。",
                stripped + ";",
            ))
        return results


class CAnalyzer(CLikeAnalyzer):
    language = "C"


class JavaAnalyzer(CLikeAnalyzer):
    language = "Java"


def _looks_like_statement(line: str) -> bool:
    if not line or line.endswith(NON_STATEMENT_ENDINGS):
        return False
    if line.startswith(("#", "@", "//", "/*", "*")):
        return False
    if CONTROL.match(line) or re.match(r"^(else|do|try|finally)\b", line):
        return False
    if re.search(r"\b(class|interface|enum|record|struct|union|namespace)\b", line):
        return False
    if re.match(r"^(public|private|protected)?\s*(static\s+)?[\w<>\[\], ?]+\s+\w+\s*\([^;]*\)\s*$", line):
        return False
    return bool(
        "=" in line
        or re.match(
            r"^(?:(?:public|private|protected|static|final|const|unsigned|signed|long|short)\s+)*"
            r"[A-Za-z_]\w*(?:\s*[*<>\[\],?]\s*\w*)*\s+[A-Za-z_]\w*\s*$",
            line,
        )
        or re.search(r"(\+\+|--|\)|\]|\b(return|break|continue|throw)\b)\s*$", line)
    )


def _sanitize_lines(source: str) -> list[str]:
    lines: list[str] = []
    in_block = False
    for raw in source.splitlines():
        output = []
        quote: str | None = None
        index = 0
        while index < len(raw):
            if in_block:
                end = raw.find("*/", index)
                if end < 0:
                    index = len(raw)
                    continue
                in_block = False
                index = end + 2
                continue
            if quote:
                if raw[index] == quote and (index == 0 or raw[index - 1] != "\\"):
                    quote = None
                output.append(" ")
                index += 1
                continue
            if raw.startswith("//", index):
                break
            if raw.startswith("/*", index):
                in_block = True
                index += 2
                continue
            if raw[index] in "\"'":
                quote = raw[index]
                output.append(" ")
            else:
                output.append(raw[index])
            index += 1
        lines.append("".join(output))
    return lines


def _deduplicate(results: list[AnalysisResult]) -> list[AnalysisResult]:
    seen = set()
    unique = []
    for result in results:
        key = (result.error_line, result.suspected_line, result.message)
        if key not in seen:
            seen.add(key)
            unique.append(result)
    return unique
