from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class AnalysisResult:
    severity: Severity
    language: str
    error_line: int
    suspected_line: int
    message: str
    reason: str
    suggestion: str

    def to_japanese_text(self) -> str:
        location = f"{self.error_line}行目付近に問題がある可能性があります。"
        if self.suspected_line != self.error_line:
            location += f"\n原因候補は{self.suspected_line}行目です。"
        return (
            f"{location}\n\n{self.message}\n\n"
            f"理由: {self.reason}\n\n修正候補:\n{self.suggestion}"
        )
