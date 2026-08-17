from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from syntax_helper.file_loader import MAX_SOURCE_SIZE, SourceFileError, load_source_file


class SourceFileLoaderTest(unittest.TestCase):
    def test_loads_utf8_and_detects_language(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sample.py"
            path.write_bytes('print("こんにちは")\n'.encode("utf-8"))

            loaded = load_source_file(str(path))

        self.assertEqual("Python", loaded.language)
        self.assertEqual('print("こんにちは")\n', loaded.source)

    def test_detects_all_supported_extensions_case_insensitively(self) -> None:
        cases = {
            "sample.C": "C",
            "sample.h": "C",
            "Sample.JAVA": "Java",
            "sample.py": "Python",
            "sample.JSON": "JSON",
        }
        with TemporaryDirectory() as directory:
            for filename, expected in cases.items():
                with self.subTest(filename=filename):
                    path = Path(directory) / filename
                    path.write_text("{}", encoding="utf-8")
                    self.assertEqual(expected, load_source_file(str(path)).language)

    def test_loads_cp932_source(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sample.c"
            path.write_bytes("// 日本語コメント\nint main(void) {}\n".encode("cp932"))
            loaded = load_source_file(str(path))
        self.assertIn("日本語コメント", loaded.source)

    def test_rejects_unsupported_extension(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_text("text", encoding="utf-8")
            with self.assertRaises(SourceFileError):
                load_source_file(str(path))

    def test_rejects_oversized_file_before_reading(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "large.c"
            with path.open("wb") as file:
                file.truncate(MAX_SOURCE_SIZE + 1)
            with self.assertRaises(SourceFileError):
                load_source_file(str(path))


if __name__ == "__main__":
    unittest.main()
