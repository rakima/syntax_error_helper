from dataclasses import dataclass
from pathlib import Path


MAX_SOURCE_SIZE = 2 * 1024 * 1024
LANGUAGE_BY_SUFFIX = {
    ".c": "C",
    ".h": "C",
    ".java": "Java",
    ".py": "Python",
    ".json": "JSON",
}


class SourceFileError(ValueError):
    """ドロップされたファイルを読み込めない場合のエラー。"""


@dataclass(frozen=True)
class LoadedSource:
    path: Path
    source: str
    language: str


def load_source_file(path_value: str) -> LoadedSource:
    path = Path(path_value)
    if not path.is_file():
        raise SourceFileError("ファイルが見つからないか、通常のファイルではありません。")

    language = LANGUAGE_BY_SUFFIX.get(path.suffix.lower())
    if language is None:
        supported = ", ".join(sorted(LANGUAGE_BY_SUFFIX))
        raise SourceFileError(f"対応していない拡張子です。対応形式: {supported}")
    if path.stat().st_size > MAX_SOURCE_SIZE:
        raise SourceFileError("ファイルが大きすぎます。2 MB以下のファイルを選択してください。")

    data = path.read_bytes()
    for encoding in ("utf-8-sig", "cp932"):
        try:
            source = data.decode(encoding)
            return LoadedSource(path.resolve(), source, language)
        except UnicodeDecodeError:
            continue
    raise SourceFileError("文字コードを読み取れませんでした。UTF-8またはCP932で保存してください。")
