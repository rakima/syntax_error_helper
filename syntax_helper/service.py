from .analyzers import CAnalyzer, JavaAnalyzer, JsonAnalyzer, PythonAnalyzer
from .model import AnalysisResult


class SyntaxAnalyzerService:
    def __init__(self) -> None:
        analyzers = (CAnalyzer(), JavaAnalyzer(), PythonAnalyzer(), JsonAnalyzer())
        self._analyzers = {analyzer.language: analyzer for analyzer in analyzers}

    @property
    def languages(self) -> tuple[str, ...]:
        return tuple(self._analyzers)

    def analyze(self, language: str, source: str) -> list[AnalysisResult]:
        try:
            analyzer = self._analyzers[language]
        except KeyError as error:
            raise ValueError(f"未対応の言語です: {language}") from error
        return analyzer.analyze(source)
