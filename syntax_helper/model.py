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

    def location_text(self) -> str:
        location = f"{self.error_line}行目付近に問題がある可能性があります。"
        if self.suspected_line != self.error_line:
            location += f"\n原因候補は{self.suspected_line}行目です。"
        return location

    def analysis_text(self) -> str:
        return f"{self.location_text()}\n\n{self.message}\n\n理由: {self.reason}"

    def suggestion_text(self) -> str:
        return f"修正候補:\n{self.suggestion}"

    def to_japanese_text(self) -> str:
        return f"{self.analysis_text()}\n\n{self.suggestion_text()}"
