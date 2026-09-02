"""Tiny Tkinter runner used by individual .pyw levels.

A level remains a standalone app. This runner only removes duplicated GUI/log/report code.
"""

from __future__ import annotations

import threading
import time
import traceback
from pathlib import Path
from typing import Callable
import tkinter as tk
from tkinter import messagebox, ttk

from .artifacts import level_artifacts_dir, open_path
from .config import load_config
from .reports import DiagReport
from .verdicts import ERROR

CheckFn = Callable[[object, DiagReport, Callable[[str], None]], None]

class LevelApp(tk.Tk):
    def __init__(self, *, level_id: str, level_name: str, purpose: str, run_checks: CheckFn):
        super().__init__()
        self.level_id = level_id
        self.level_name = level_name
        self.purpose = purpose
        self.run_checks = run_checks
        self.config = load_config()
        self.artifact_dir = level_artifacts_dir(self.config.artifacts_root_path, level_id, level_name)
        self.report = DiagReport.new(
            level=level_id,
            name=level_name,
            app_name=self.config.app_name,
            target_repo_root=str(self.config.target_root_path),
            frontend_url=self.config.frontend_url,
            backend_url=self.config.backend_url,
        )
        self.status_var = tk.StringVar(value="Prêt")
        self.title(f"LevelUpDiag {level_id} — {level_name}")
        self.geometry("980x680")
        self.minsize(820, 540)
        self._build_ui()
        self.log(f"Config: {self.config.config_path}")
        self.log(f"App: {self.config.app_name}")
        self.log(f"Target: {self.config.target_root_path}")

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        outer = ttk.Frame(self, padding=12)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=1)
        ttk.Label(outer, text=f"{self.level_id} — {self.level_name}", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(outer, text=self.purpose, foreground="#666666", wraplength=900).grid(row=1, column=0, sticky="w", pady=(2, 10))
        bar = ttk.Frame(outer)
        bar.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(bar, text="Lancer ce niveau", command=self.run_async).pack(side="left")
        ttk.Button(bar, text="Ouvrir artefacts", command=lambda: open_path(self.artifact_dir)).pack(side="left", padx=6)
        ttk.Button(bar, text="Copier log", command=self.copy_log).pack(side="left", padx=6)
        ttk.Button(bar, text="Vider log", command=self.clear_log).pack(side="left", padx=6)
        ttk.Label(bar, textvariable=self.status_var).pack(side="right")
        frame = ttk.LabelFrame(outer, text="Journal")
        frame.grid(row=3, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(frame, wrap="word", font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(frame, command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)

    def log(self, message: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {message}\n"
        def append():
            self.log_text.insert("end", line)
            self.log_text.see("end")
        try:
            self.after(0, append)
        except RuntimeError:
            pass

    def copy_log(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.log_text.get("1.0", "end").strip())

    def clear_log(self) -> None:
        self.log_text.delete("1.0", "end")

    def run_async(self) -> None:
        self.status_var.set("RUNNING")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self) -> None:
        try:
            self.run_checks(self.config, self.report, self.log)
        except Exception as exc:
            self.report.add("level.exception", ERROR, "runner", f"{type(exc).__name__}: {exc}", evidence=traceback.format_exc())
            self.log(traceback.format_exc())
        finally:
            json_path = self.artifact_dir / f"{self.level_id}-report.json"
            txt_path = self.artifact_dir / f"{self.level_id}-report.txt"
            self.report.write_json(json_path)
            self.report.write_txt(txt_path)
            self.log(f"Verdict: {self.report.verdict}")
            self.log(f"Rapport JSON: {json_path}")
            self.log(f"Rapport TXT: {txt_path}")
            self.status_var.set(self.report.verdict)


def run_level_app(level_id: str, level_name: str, purpose: str, run_checks: CheckFn) -> None:
    app = LevelApp(level_id=level_id, level_name=level_name, purpose=purpose, run_checks=run_checks)
    app.mainloop()
