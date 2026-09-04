from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any

TOOL_ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = TOOL_ROOT / "levelupdiag_manifest.json"
CONFIG_CANDIDATES = (
    TOOL_ROOT / "levelupdiag.config.local.json",
    TOOL_ROOT / "levelupdiag.config.json",
    TOOL_ROOT / "levelupdiag.config.example.json",
)


class LevelUpDiagConsole(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Konnaxion LevelUpDiag — Console de tests")
        self.geometry("1080x840")
        self.minsize(920, 700)

        self.process: subprocess.Popen[str] | None = None
        self.output_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.manifest: dict[str, Any] = {}
        self.level_vars: dict[str, tk.BooleanVar] = {}
        self.level_data: dict[str, dict[str, Any]] = {}
        self.campaign_var = tk.StringVar(value="connection-debug")
        self.status_var = tk.StringVar(value="Prêt")
        self.selection_var = tk.StringVar(value="Sélection: —")
        self.evidence_var = tk.StringVar(value="Preuves: —")

        self._build_ui()
        self._load_manifest()
        self.after(80, self._poll_output)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x")
        ttk.Label(
            header,
            text="Konnaxion LevelUpDiag",
            font=("Segoe UI", 15, "bold"),
        ).pack(side="left")
        ttk.Label(header, textvariable=self.status_var).pack(side="right")

        ttk.Label(
            outer,
            text=(
                "Choisis une campagne prédéfinie ou sélectionne directement les niveaux N00..N11. "
                "Les niveaux sont exécutés dans l'ordre défini par le manifest LevelUpDiag."
            ),
            wraplength=1020,
        ).pack(anchor="w", pady=(4, 10))

        campaign_box = ttk.LabelFrame(outer, text="Campagnes")
        campaign_box.pack(fill="x", pady=(0, 8))
        campaign_box.columnconfigure(1, weight=1)

        ttk.Label(campaign_box, text="Campagne").grid(
            row=0, column=0, sticky="w", padx=(10, 6), pady=8
        )
        self.campaign_combo = ttk.Combobox(
            campaign_box,
            textvariable=self.campaign_var,
            state="readonly",
        )
        self.campaign_combo.grid(row=0, column=1, sticky="ew", padx=6, pady=8)
        self.campaign_combo.bind("<<ComboboxSelected>>", self._campaign_changed)
        ttk.Button(
            campaign_box,
            text="SÉLECTIONNER CAMPAGNE",
            command=self._select_current_campaign,
        ).grid(row=0, column=2, padx=6, pady=8)
        ttk.Button(
            campaign_box,
            text="LANCER CAMPAGNE",
            command=self._run_campaign,
        ).grid(row=0, column=3, padx=(6, 10), pady=8)

        preset_row = ttk.Frame(campaign_box)
        preset_row.grid(row=1, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 8))
        self.preset_frame = preset_row

        self.campaign_description_var = tk.StringVar(value="")
        ttk.Label(
            campaign_box,
            textvariable=self.campaign_description_var,
            wraplength=1000,
        ).grid(row=2, column=0, columnspan=4, sticky="w", padx=10, pady=(0, 8))

        level_box = ttk.LabelFrame(outer, text="Tests / niveaux")
        level_box.pack(fill="x", pady=(0, 8))
        self.level_frame = level_box

        selection_actions = ttk.Frame(outer)
        selection_actions.pack(fill="x", pady=(0, 6))
        ttk.Button(selection_actions, text="TOUS", command=self._select_all).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(selection_actions, text="AUCUN", command=self._select_none).pack(
            side="left", padx=6
        )
        ttk.Button(
            selection_actions,
            text="CONNECTION DEBUG",
            command=lambda: self._select_campaign("connection-debug"),
        ).pack(side="left", padx=6)
        ttk.Label(selection_actions, textvariable=self.selection_var).pack(
            side="right", padx=(12, 0)
        )

        self.purpose_var = tk.StringVar(value="")
        ttk.Label(outer, textvariable=self.purpose_var, wraplength=1020).pack(
            anchor="w", pady=(0, 8)
        )

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(0, 8))
        self.run_button = ttk.Button(
            actions,
            text="LANCER LA SÉLECTION",
            command=self._run_selected,
        )
        self.run_button.pack(side="left", padx=(0, 6))
        self.stop_button = ttk.Button(
            actions,
            text="ARRÊTER",
            command=self._stop,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=6)
        ttk.Button(actions, text="EFFACER CONSOLE", command=self._clear_console).pack(
            side="left", padx=6
        )
        ttk.Button(
            actions,
            text="OUVRIR PREUVES",
            command=self._open_evidence_folder,
        ).pack(side="left", padx=6)

        ttk.Label(outer, textvariable=self.evidence_var).pack(anchor="w", pady=(0, 8))

        ttk.Label(outer, text="Console", font=("Segoe UI", 10, "bold")).pack(
            anchor="w", pady=(2, 4)
        )
        self.console = ScrolledText(outer, wrap="word", height=25, font=("Consolas", 10))
        self.console.pack(fill="both", expand=True)
        self.console.configure(state="disabled")

    def _load_manifest(self) -> None:
        try:
            self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            messagebox.showerror(
                "LevelUpDiag",
                f"Impossible de charger {MANIFEST_PATH.name}:\n{exc}",
            )
            self.run_button.configure(state="disabled")
            return

        levels = sorted(
            self.manifest.get("levels", []),
            key=lambda item: (item.get("order", 0), item.get("id", "")),
        )
        if not levels:
            messagebox.showerror("LevelUpDiag", "Aucun niveau déclaré dans le manifest.")
            self.run_button.configure(state="disabled")
            return

        for index, level in enumerate(levels):
            level_id = str(level["id"])
            self.level_data[level_id] = level
            var = tk.BooleanVar(value=False)
            var.trace_add("write", lambda *_args: self._selection_changed())
            self.level_vars[level_id] = var
            ttk.Checkbutton(
                self.level_frame,
                text=f"{level_id}  {level.get('name', '')}",
                variable=var,
            ).grid(
                row=index // 2,
                column=index % 2,
                sticky="w",
                padx=12,
                pady=5,
            )

        self.level_frame.columnconfigure(0, weight=1)
        self.level_frame.columnconfigure(1, weight=1)

        campaigns = self.manifest.get("campaigns", {})
        campaign_names = list(campaigns.keys())
        self.campaign_combo["values"] = campaign_names
        if "connection-debug" in campaigns:
            self.campaign_var.set("connection-debug")
        elif campaign_names:
            self.campaign_var.set(campaign_names[0])

        for widget in self.preset_frame.winfo_children():
            widget.destroy()
        preferred = (
            ("SOURCE AUDIT", "source-audit"),
            ("AUTH DEBUG", "auth-debug"),
            ("CONNECTION DEBUG", "connection-debug"),
            ("FULL LOCAL", "full-local"),
        )
        shown = 0
        for label, campaign in preferred:
            if campaign not in campaigns:
                continue
            ttk.Button(
                self.preset_frame,
                text=label,
                command=lambda name=campaign: self._select_campaign(name),
            ).pack(side="left", padx=(0 if shown == 0 else 6, 6))
            shown += 1

        self._select_current_campaign()
        self._refresh_evidence_path()

    def _campaign_changed(self, _event: object | None = None) -> None:
        campaign = self.campaign_var.get()
        data = self.manifest.get("campaigns", {}).get(campaign, {})
        self.campaign_description_var.set(str(data.get("description", "")))

    def _select_current_campaign(self) -> None:
        self._select_campaign(self.campaign_var.get())

    def _select_campaign(self, campaign: str) -> None:
        campaigns = self.manifest.get("campaigns", {})
        data = campaigns.get(campaign)
        if not isinstance(data, dict):
            return
        wanted = set(data.get("levels", []))
        for level_id, var in self.level_vars.items():
            var.set(level_id in wanted)
        self.campaign_var.set(campaign)
        self._campaign_changed()

    def _select_all(self) -> None:
        for var in self.level_vars.values():
            var.set(True)

    def _select_none(self) -> None:
        for var in self.level_vars.values():
            var.set(False)

    def _selected_levels(self) -> list[str]:
        ordered = sorted(
            self.level_data,
            key=lambda level_id: (
                self.level_data[level_id].get("order", 0),
                level_id,
            ),
        )
        return [level_id for level_id in ordered if self.level_vars[level_id].get()]

    def _selection_changed(self) -> None:
        selected = self._selected_levels()
        self.selection_var.set(
            "Sélection: " + (" → ".join(selected) if selected else "—")
        )
        purposes = [
            f"{level_id}: {self.level_data[level_id].get('purpose', '')}"
            for level_id in selected
        ]
        self.purpose_var.set(" | ".join(purposes))

    def _python_executable(self) -> str:
        executable = Path(sys.executable)
        if os.name == "nt" and executable.name.lower() == "pythonw.exe":
            console_python = executable.with_name("python.exe")
            if console_python.exists():
                return str(console_python)
        return str(executable)

    def _run_campaign(self) -> None:
        campaign = self.campaign_var.get().strip()
        if not campaign:
            messagebox.showwarning("LevelUpDiag", "Aucune campagne sélectionnée.")
            return
        self._start_command(["run", campaign], f"campagne {campaign}")

    def _run_selected(self) -> None:
        selected = self._selected_levels()
        if not selected:
            messagebox.showwarning("LevelUpDiag", "Sélectionne au moins un test/niveau.")
            return
        selection = ",".join(selected)
        self._start_command(["run", selection], selection)

    def _start_command(self, arguments: list[str], label: str) -> None:
        if self.process is not None:
            messagebox.showinfo("LevelUpDiag", "Un diagnostic est déjà en cours.")
            return

        runner = TOOL_ROOT / "levelupdiag.py"
        if not runner.is_file():
            messagebox.showerror("LevelUpDiag", f"Lanceur introuvable:\n{runner}")
            return

        command = [self._python_executable(), str(runner), *arguments]
        self._append(f"\n$ {' '.join(command)}\n")
        self.status_var.set(f"Exécution: {label}")
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        threading.Thread(target=self._worker, args=(command,), daemon=True).start()

    def _worker(self, command: list[str]) -> None:
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            process = subprocess.Popen(
                command,
                cwd=str(TOOL_ROOT),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                shell=False,
                creationflags=creationflags,
            )
            self.process = process
            assert process.stdout is not None
            for line in process.stdout:
                self.output_queue.put(("line", line))
            self.output_queue.put(("done", process.wait()))
        except Exception as exc:
            self.output_queue.put(("error", str(exc)))
        finally:
            self.process = None

    def _poll_output(self) -> None:
        try:
            while True:
                kind, payload = self.output_queue.get_nowait()
                if kind == "line":
                    self._append(str(payload))
                elif kind == "done":
                    code = int(payload)
                    self._append(f"\n[Terminé — code {code}]\n")
                    self.status_var.set(f"Terminé — code {code}")
                    self.run_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self._refresh_evidence_path()
                elif kind == "error":
                    self._append(f"\n[ERREUR] {payload}\n")
                    self.status_var.set("Erreur")
                    self.run_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._poll_output)

    def _stop(self) -> None:
        process = self.process
        if process is None:
            return
        if not messagebox.askyesno("LevelUpDiag", "Arrêter le diagnostic en cours ?"):
            return
        try:
            process.terminate()
            self._append("\n[Arrêt demandé]\n")
            self.status_var.set("Arrêt demandé")
        except OSError as exc:
            messagebox.showerror("LevelUpDiag", str(exc))

    def _clear_console(self) -> None:
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")

    def _append(self, text: str) -> None:
        self.console.configure(state="normal")
        self.console.insert("end", text)
        self.console.see("end")
        self.console.configure(state="disabled")

    def _load_config(self) -> dict[str, Any]:
        for path in CONFIG_CANDIDATES:
            if path.is_file():
                try:
                    data = json.loads(path.read_text(encoding="utf-8-sig"))
                    if isinstance(data, dict):
                        return data
                except (OSError, json.JSONDecodeError):
                    continue
        return {}

    @staticmethod
    def _looks_like_konnaxion(path: Path) -> bool:
        return (path / "frontend").is_dir() and (path / "backend").is_dir()

    def _target_repo_root(self) -> Path | None:
        cfg = self._load_config()
        raw = cfg.get("target_repo_root", "auto")
        if isinstance(raw, str) and raw.strip() and raw.strip().lower() != "auto":
            candidate = Path(os.path.expandvars(raw)).expanduser()
            if not candidate.is_absolute():
                candidate = TOOL_ROOT / candidate
            return candidate.resolve()

        candidates = (
            TOOL_ROOT,
            TOOL_ROOT.parent,
            TOOL_ROOT.parent / "Konnaxion",
            TOOL_ROOT.parent.parent / "Konnaxion",
        )
        for candidate in candidates:
            try:
                resolved = candidate.resolve()
            except OSError:
                continue
            if self._looks_like_konnaxion(resolved):
                return resolved
        return None

    def _evidence_folder(self) -> Path | None:
        target = self._target_repo_root()
        if target is None:
            return None
        cfg = self._load_config()
        control_name = cfg.get("control_dir", ".levelupdiag")
        if not isinstance(control_name, str) or not control_name.strip():
            control_name = ".levelupdiag"
        return target / control_name / "current"

    def _refresh_evidence_path(self) -> None:
        folder = self._evidence_folder()
        self.evidence_var.set(f"Preuves: {folder}" if folder else "Preuves: cible auto non résolue")

    def _open_evidence_folder(self) -> None:
        folder = self._evidence_folder()
        if folder is None or not folder.exists():
            messagebox.showwarning(
                "LevelUpDiag",
                f"Dossier de preuves introuvable:\n{folder or 'cible non résolue'}",
            )
            return
        try:
            if os.name == "nt":
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except OSError as exc:
            messagebox.showerror("LevelUpDiag", f"Ouverture impossible:\n{exc}")

    def _on_close(self) -> None:
        if self.process is not None:
            if not messagebox.askyesno(
                "LevelUpDiag",
                "Un diagnostic est en cours. Fermer quand même ?",
            ):
                return
            try:
                self.process.terminate()
            except OSError:
                pass
        self.destroy()


if __name__ == "__main__":
    LevelUpDiagConsole().mainloop()
