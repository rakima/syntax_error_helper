from dataclasses import dataclass

from .model import AnalysisResult, Severity


@dataclass(frozen=True)
class ScanConfig:
    line_comments: tuple[str, ...] = ()
    block_comments: tuple[tuple[str, str], ...] = ()
    quote_chars: tuple[str, ...] = ('"', "'")
    triple_quotes: bool = False


@dataclass(frozen=True)
class TokenIssue:
    kind: str
    line: int
    related_line: int
    symbol: str
    expected: str


PAIRS = {"(": ")", "[": "]", "{": "}"}
REVERSE_PAIRS = {value: key for key, value in PAIRS.items()}


def scan_structure(source: str, config: ScanConfig) -> list[TokenIssue]:
    """文字列とコメントを除外し、対応記号をスタックで検査する。"""
    issues: list[TokenIssue] = []
    stack: list[tuple[str, int]] = []
    lines = source.splitlines() or [""]
    quote: str | None = None
    quote_line = 0
    block_end: str | None = None
    block_line = 0

    for line_no, line in enumerate(lines, 1):
        index = 0
        while index < len(line):
            if block_end:
                end_index = line.find(block_end, index)
                if end_index < 0:
                    break
                end_length = len(block_end)
                block_end = None
                index = end_index + end_length
                continue

            if quote:
                if line.startswith(quote, index) and not _is_escaped(line, index):
                    index += len(quote)
                    quote = None
                    continue
                index += 1
                continue

            comment = next((marker for marker in config.line_comments if line.startswith(marker, index)), None)
            if comment:
                break
            block = next((pair for pair in config.block_comments if line.startswith(pair[0], index)), None)
            if block:
                block_end = block[1]
                block_line = line_no
                index += len(block[0])
                continue

            triple = line[index:index + 3]
            if config.triple_quotes and triple in ('"""', "'''"):
                quote, quote_line = triple, line_no
                index += 3
                continue
            char = line[index]
            if char in config.quote_chars:
                quote, quote_line = char, line_no
                index += 1
                continue
            if char in PAIRS:
                stack.append((char, line_no))
            elif char in REVERSE_PAIRS:
                if stack and stack[-1][0] == REVERSE_PAIRS[char]:
                    stack.pop()
                else:
                    related = stack[-1][1] if stack else line_no
                    issues.append(TokenIssue("unexpected_closer", line_no, related, char, REVERSE_PAIRS[char]))
            index += 1

        if quote and len(quote) == 1:
            issues.append(TokenIssue("unclosed_string", line_no, quote_line, quote, quote))
            quote = None

    last_line = len(lines)
    if quote:
        issues.append(TokenIssue("unclosed_string", last_line, quote_line, quote, quote))
    if block_end:
        issues.append(TokenIssue("unclosed_comment", last_line, block_line, block_end, block_end))
    for opener, line_no in reversed(stack):
        issues.append(TokenIssue("unclosed_opener", last_line, line_no, opener, PAIRS[opener]))
    return issues


def structure_results(source: str, language: str, config: ScanConfig) -> list[AnalysisResult]:
    results: list[AnalysisResult] = []
    for issue in scan_structure(source, config):
        if issue.kind == "unclosed_opener":
            message = f"{issue.related_line}行目で開始した「{issue.symbol}」が閉じられていない可能性があります。"
            reason = f"対応する「{issue.expected}」が見つかりません。"
            suggestion = f"{issue.line}行目付近に「{issue.expected}」を追加できるか確認してください。"
        elif issue.kind == "unexpected_closer":
            message = f"「{issue.symbol}」に対応する開始記号が見つからない可能性があります。"
            reason = "閉じ記号が多いか、開始記号が不足しています。"
            suggestion = f"{issue.line}行目の「{issue.symbol}」と、その前の行を確認してください。"
        elif issue.kind == "unclosed_comment":
            message = f"{issue.related_line}行目で開始したコメントが閉じられていない可能性があります。"
            reason = f"コメント終了記号「{issue.expected}」が見つかりません。"
            suggestion = f"コメントの末尾に「{issue.expected}」を追加してください。"
        else:
            name = "文字列" if issue.symbol == '"' else "文字"
            message = f"{issue.related_line}行目の{name}リテラルが閉じられていない可能性があります。"
            reason = f"開始した「{issue.symbol}」に対応する終了記号がありません。"
            suggestion = f"{issue.related_line}行目に「{issue.expected}」を追加できるか確認してください。"
        results.append(AnalysisResult(Severity.ERROR, language, issue.line, issue.related_line, message, reason, suggestion))
    return results


def _is_escaped(line: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and line[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1
