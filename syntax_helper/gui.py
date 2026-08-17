import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

from tkinterdnd2 import DND_FILES, TkinterDnD

from .file_loader import SourceFileError, load_source_file
from .model import AnalysisResult
from .service import SyntaxAnalyzerService


class LineNumberedEditor(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.editor_font = tkfont.Font(family="Consolas", size=11)
        shared_layout = {
            "font": self.editor_font,
            "borderwidth": 0,
            "highlightthickness": 0,
            "spacing1": 0,
            "spacing2": 0,
            "spacing3": 0,
        }
        self.line_numbers = tk.Text(
            self,
            width=5,
            padx=4,
            takefocus=False,
            wrap="none",
            background="#f0f0f0",
            foreground="#666666",
            state="disabled",
            **shared_layout,
        )
        self.text = tk.Text(self, wrap="none", undo=True, **shared_layout)
        vertical = ttk.Scrollbar(self, orient="vertical", command=self._scroll_both)
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=lambda first, last: self._on_scroll(vertical, first, last),
                            xscrollcommand=horizontal.set)
        self.line_numbers.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")
        vertical.grid(row=0, column=2, sticky="ns")
        horizontal.grid(row=1, column=1, sticky="ew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<Configure>", lambda _event: self.update_line_numbers())
        self.text.tag_configure("suspected", background="#ffe1e1")
        self.text.tag_configure("error", background="#fff0f0")
        self.update_line_numbers()

    def _scroll_both(self, *args: str) -> None:
        self.text.yview(*args)
        self.line_numbers.yview(*args)

    def _on_scroll(self, scrollbar: ttk.Scrollbar, first: str, last: str) -> None:
        scrollbar.set(first, last)
        self.line_numbers.yview_moveto(first)

    def _on_modified(self, _event: tk.Event) -> None:
        if self.text.edit_modified():
            self.update_line_numbers()
            self.text.edit_modified(False)

    def update_line_numbers(self) -> None:
        count = int(self.text.index("end-1c").split(".")[0])
        content = "\n".join(str(number) for number in range(1, count + 1))
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", content)
        self.line_numbers.configure(state="disabled")

    def get(self) -> str:
        return self.text.get("1.0", "end-1c")

    def set_content(self, source: str) -> None:
        self.text.tag_remove("error", "1.0", "end")
        self.text.tag_remove("suspected", "1.0", "end")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", source)
        self.text.edit_modified(False)
        self.update_line_numbers()

    def highlight(self, results: list[AnalysisResult]) -> None:
        self.text.tag_remove("error", "1.0", "end")
        self.text.tag_remove("suspected", "1.0", "end")
        for result in results:
            self._tag_line(result.error_line, "error")
            self._tag_line(result.suspected_line, "suspected")

    def _tag_line(self, line: int, tag: str) -> None:
        last_line = int(self.text.index("end-1c").split(".")[0])
        if 1 <= line <= last_line:
            self.text.tag_add(tag, f"{line}.0", f"{line}.end+1c")


class SyntaxErrorHelperApp(TkinterDnD.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("構文エラー解析ツール")
        self.geometry("1000x720")
        self.minsize(720, 520)
        self.service = SyntaxAnalyzerService()
        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=(10, 10, 10, 6))
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="言語:").pack(side="left")
        self.language = tk.StringVar(value=self.service.languages[0])
        selector = ttk.Combobox(toolbar, textvariable=self.language,
                                values=self.service.languages, state="readonly", width=12)
        selector.pack(side="left", padx=(6, 12))
        ttk.Button(toolbar, text="解析", command=self._analyze).pack(side="left")
        ttk.Label(toolbar, text="入力コードは実行されません。", foreground="#666666").pack(side="right")

        self.status = tk.StringVar(value="対応ファイルをエディタへドラッグ＆ドロップして読み込めます。")
        ttk.Label(self, textvariable=self.status, foreground="#555555", padding=(10, 0, 10, 6)).pack(fill="x")

        pane = ttk.Panedwindow(self, orient="vertical")
        pane.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        editor_frame = ttk.LabelFrame(pane, text="ソースコード", padding=4)
        self.editor = LineNumberedEditor(editor_frame)
        self.editor.pack(fill="both", expand=True)
        for drop_target in (self.editor.text, self.editor.line_numbers):
            drop_target.drop_target_register(DND_FILES)
            drop_target.dnd_bind("<<Drop>>", self._on_file_drop)
        pane.add(editor_frame, weight=3)

        result_frame = ttk.LabelFrame(pane, text="解析結果・修正候補", padding=4)
        self.result = tk.Text(result_frame, wrap="word", height=12, state="disabled",
                              background="#fafafa", font=("Yu Gothic UI", 10))
        result_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.result.yview)
        self.result.configure(yscrollcommand=result_scroll.set)
        self.result.pack(side="left", fill="both", expand=True)
        result_scroll.pack(side="right", fill="y")
        pane.add(result_frame, weight=2)

    def _on_file_drop(self, event: tk.Event) -> str:
        paths = self.tk.splitlist(event.data)
        if not paths:
            return event.action
        try:
            loaded = load_source_file(paths[0])
        except (OSError, SourceFileError) as error:
            messagebox.showerror("ファイルを読み込めません", str(error), parent=self)
            return event.action

        self.editor.set_content(loaded.source)
        self.language.set(loaded.language)
        self.editor.text.focus_set()
        suffix = "（最初の1ファイルを読み込みました）" if len(paths) > 1 else ""
        self.status.set(f"{loaded.path.name} を読み込みました。{suffix}")
        self._clear_results()
        return event.action

    def _clear_results(self) -> None:
        self.result.configure(state="normal")
        self.result.delete("1.0", "end")
        self.result.configure(state="disabled")

    def _analyze(self) -> None:
        results = self.service.analyze(self.language.get(), self.editor.get())
        self.editor.highlight(results)
        if results:
            content = "\n\n" + ("\n\n" + "─" * 40 + "\n\n").join(
                result.to_japanese_text() for result in results
            )
        else:
            content = "構文エラー候補は見つかりませんでした。"
        self.result.configure(state="normal")
        self.result.delete("1.0", "end")
        self.result.insert("1.0", content.strip())
        self.result.configure(state="disabled")


def run() -> None:
    SyntaxErrorHelperApp().mainloop()
