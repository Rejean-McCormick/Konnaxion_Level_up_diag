"""Tkinter control surface for LevelUpDiag-Koali.

The wrapper is intentionally presentation-only.  Planning, dependencies,
execution and verdict semantics remain in ``levelupdiag_core``.
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import messagebox, ttk
from collections.abc import Callable

from levelupdiag_core.models import CampaignResult, LevelResult
from levelupdiag_wrapper_common import (
    BackgroundTask,
    LevelRow,
    format_campaign_result,
    format_level_result,
    level_rows,
    load_gui_state,
    open_logs,
    run_enabled,
    run_one,
)


class LevelUpDiagApp(ttk.Frame):
    """Thin Tk presentation over the shared LevelUpDiag-Koali core."""

    POLL_MS = 100

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=10)
        self.master = master
        self.config_state = None
        self.levels = []
        self._rows_by_id: dict[str, LevelRow] = {}
        self._task: BackgroundTask[LevelResult | CampaignResult] | None = None

        self.status_var = tk.StringVar(master=master, value="Loading…")
        self._build_widgets()
        self.reload_state(show_dialog=False)

    def _build_widgets(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for column in range(6):
            toolbar.columnconfigure(column, weight=0)
        toolbar.columnconfigure(6, weight=1)

        self.reload_button = ttk.Button(toolbar, text="Reload", command=self.reload_state)
        self.reload_button.grid(row=0, column=0, padx=(0, 6))
        self.run_button = ttk.Button(toolbar, text="Run selected", command=self.run_selected)
        self.run_button.grid(row=0, column=1, padx=(0, 6))
        self.run_all_button = ttk.Button(toolbar, text="Run all enabled", command=self.run_all)
        self.run_all_button.grid(row=0, column=2, padx=(0, 6))
        self.logs_button = ttk.Button(toolbar, text="Open logs", command=self.open_selected_logs)
        self.logs_button.grid(row=0, column=3, padx=(0, 6))
        ttk.Button(toolbar, text="Quit", command=self.master.destroy).grid(row=0, column=4)

        columns = ("enabled", "required", "verdict")
        self.tree = ttk.Treeview(self, columns=columns, show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Level")
        self.tree.heading("enabled", text="Enabled")
        self.tree.heading("required", text="Required")
        self.tree.heading("verdict", text="Last verdict")
        self.tree.column("#0", width=360, minwidth=220, stretch=True)
        self.tree.column("enabled", width=80, anchor="center", stretch=False)
        self.tree.column("required", width=80, anchor="center", stretch=False)
        self.tree.column("verdict", width=120, anchor="center", stretch=False)
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda _event: self.run_selected())

        status = ttk.Label(self, textvariable=self.status_var, anchor="w")
        status.grid(row=2, column=0, sticky="ew", pady=(8, 4))

        output_frame = ttk.LabelFrame(self, text="Last run", padding=4)
        output_frame.grid(row=3, column=0, sticky="nsew")
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)
        self.output = tk.Text(output_frame, height=12, wrap="word", state="disabled")
        self.output.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.output.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output.configure(yscrollcommand=scrollbar.set)

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        for button in (self.reload_button, self.run_button, self.run_all_button, self.logs_button):
            button.configure(state=state)

    def _write_output(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")

    def _selected_level(self):
        selection = self.tree.selection()
        if not selection:
            return None
        row = self._rows_by_id.get(selection[0])
        return row.level if row is not None else None

    def _populate_tree(self, rows: list[LevelRow]) -> None:
        selected = self.tree.selection()[0] if self.tree.selection() else None
        self.tree.delete(*self.tree.get_children())
        self._rows_by_id = {row.level.id: row for row in rows}
        for row in rows:
            level = row.level
            self.tree.insert(
                "",
                "end",
                iid=level.id,
                text=level.display_title,
                values=(row.enabled_text, row.required_text, row.last_verdict),
            )
        if selected and self.tree.exists(selected):
            self.tree.selection_set(selected)
        elif rows:
            self.tree.selection_set(rows[0].level.id)

    def reload_state(self, show_dialog: bool = True) -> None:
        if self._task is not None and self._task.running:
            return
        try:
            config, levels = load_gui_state()
            rows = level_rows(config, levels)
        except Exception as exc:
            self.status_var.set(f"Reload failed: {exc}")
            if show_dialog:
                messagebox.showerror("LevelUpDiag-Koali", str(exc), parent=self.master)
            return

        self.config_state = config
        self.levels = levels
        self._populate_tree(rows)
        self.status_var.set(
            f"{config.app_name} · {len(levels)} levels · target: {config.target_root_path}"
        )

    def _start_task(
        self,
        description: str,
        target: Callable[[], LevelResult | CampaignResult],
    ) -> None:
        if self._task is not None and self._task.running:
            return
        self._task = BackgroundTask(target)
        self._set_busy(True)
        self.status_var.set(description)
        self._task.start()
        self.after(self.POLL_MS, self._poll_task)

    def _poll_task(self) -> None:
        task = self._task
        if task is None:
            return
        message = task.poll()
        if message is None:
            if task.running:
                self.after(self.POLL_MS, self._poll_task)
                return
            # Defensive: the worker always queues a terminal message.
            self._set_busy(False)
            self.status_var.set("Run ended without a result")
            self._task = None
            return

        self._task = None
        self._set_busy(False)
        if message.kind == "error":
            exc = message.payload
            self.status_var.set(f"Run failed: {exc}")
            self._write_output(f"{type(exc).__name__}: {exc}")
            messagebox.showerror("LevelUpDiag-Koali", str(exc), parent=self.master)
            self.reload_state(show_dialog=False)
            return

        result = message.payload
        final_status: str
        if isinstance(result, LevelResult):
            final_status = f"{result.level}: {result.verdict}"
            self._write_output(format_level_result(result))
        elif isinstance(result, CampaignResult):
            final_status = f"Campaign {result.campaign}: {result.verdict}"
            self._write_output(format_campaign_result(result))
        else:
            final_status = "Runner returned an unsupported result"
            self._write_output(repr(result))
        self.reload_state(show_dialog=False)
        self.status_var.set(final_status)

    def run_selected(self) -> None:
        level = self._selected_level()
        if level is None:
            messagebox.showinfo("LevelUpDiag-Koali", "Select a level first.", parent=self.master)
            return
        if self.config_state is None:
            self.reload_state()
            if self.config_state is None:
                return
        config = self.config_state
        self._start_task(f"Running {level.display_title}…", lambda: run_one(level, config))

    def run_all(self) -> None:
        if self.config_state is None:
            self.reload_state()
            if self.config_state is None:
                return
        config = self.config_state
        levels = list(self.levels)
        self._start_task("Running all enabled levels…", lambda: run_enabled(levels, config))

    def open_selected_logs(self) -> None:
        if self.config_state is None:
            self.reload_state()
            if self.config_state is None:
                return
        try:
            open_logs(self.config_state, self._selected_level())
        except Exception as exc:
            self.status_var.set(f"Could not open logs: {exc}")
            messagebox.showerror("LevelUpDiag-Koali", str(exc), parent=self.master)


def create_app() -> tuple[tk.Tk, LevelUpDiagApp]:
    """Create, but do not run, the Tk application."""

    root = tk.Tk()
    root.title("LevelUpDiag-Koali")
    root.minsize(760, 520)
    app = LevelUpDiagApp(root)
    return root, app


def main() -> int:
    try:
        root, _app = create_app()
    except tk.TclError as exc:
        print(f"LevelUpDiag-Koali GUI unavailable: {exc}", file=sys.stderr)
        return 3
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
