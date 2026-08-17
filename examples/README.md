# 検証用サンプルコード

各言語について、エラーがない `valid` と典型的な間違いを含む `syntax_errors` を用意しています。ファイルの内容をGUIへ貼り付け、対応する言語を選択して「解析」を押してください。

| 言語 | 正常例 | エラー例 | エラー例の主な確認項目 |
| --- | --- | --- | --- |
| C | `c/valid.c` | `c/syntax_errors.c` | セミコロン、`for`、`)`、`}` |
| Java | `java/ValidSample.java` | `java/SyntaxErrors.java` | セミコロン、`for`、`)`、`}` |
| Python | `python/valid.py` | `python/syntax_errors.py` | `:`、`=` / `==`、インデント、`)` |
| JSON | `json/valid.json` | `json/syntax_errors.json` | カンマ、キーの引用符、末尾カンマ、`}` |

エラー例は複数の候補を表示する確認用であり、意図的に実行・コンパイルできない内容になっています。
