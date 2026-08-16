from abc import ABC, abstractmethod

from syntax_helper.model import AnalysisResult


class LanguageAnalyzer(ABC):
    language: str

    @abstractmethod
    def analyze(self, source: str) -> list[AnalysisResult]:
        """コードを実行せず、構文エラー候補を返す。"""
