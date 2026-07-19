"""Russian desktop UI for the research-only standalone beam workflow.

The view is deliberately thin: it contains no engineering formulas and calls
the existing :func:`run_standalone_beam_case` controller directly.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import sys
import threading
import time
import webbrowser
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from sp63_core.materials.rebar import REBAR_CATALOG, STIRRUP_DIAMETERS
from sp63_core.materials.uls_context import (
    SUPPORTED_ULS_CONCRETE_CLASSES,
    SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES,
)
from sp63_core.standalone import (
    StandaloneBeamInput,
    StandaloneRunResult,
    run_standalone_beam_case,
)
from sp63_core.standalone.app import load_standalone_input
from sp63_core.standalone.gui_logic import (
    FORM_FIELDS,
    next_output_dir,
    parse_form_values,
    status_view_model,
    verify_gui_result,
    verify_review_bundle,
)

APP_TITLE = "ЖБК — инженерная исследовательская проверка"
SAFETY_BANNER = (
    "ИССЛЕДОВАТЕЛЬСКАЯ ВЕРСИЯ. Не использовать для проектных решений.\n"
    "Программа не утверждает несущую способность. Требуется проверка "
    "квалифицированным инженером."
)
FOOTER_TEXT = (
    "project_use=false  ·  requires_engineer_review=true  ·  "
    "подбор арматуры: diagnostic_only"
)
DEMO_VALUES = {
    "case_id": "beam-001",
    "b_mm": "300",
    "h_mm": "500",
    "cover_mm": "32",
    "stirrup_diameter_mm": "8",
    "concrete_class": "B25",
    "longitudinal_rebar_class": "A500",
    "stirrup_rebar_class": "A240",
    "moment_kNm": "150",
    "shear_kN": "80",
    "tension_face": "",
}


class _HeadlessMessageBox:
    """Prevent modal dialogs from blocking an automated hidden-window smoke."""

    @staticmethod
    def showerror(*_args: object, **_kwargs: object) -> None:
        return None

    showinfo = showerror
    showwarning = showerror


def _tk_modules() -> dict[str, Any]:
    """Import Tk lazily so non-GUI/headless standalone imports remain safe."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk

    return {
        "tk": tk,
        "ttk": ttk,
        "filedialog": filedialog,
        "messagebox": messagebox,
        "scrolledtext": scrolledtext,
    }


class EngineerGui:
    """One-window presenter over the existing standalone controller."""

    def __init__(self, root: Any, output_root: Path, modules: dict[str, Any] | None = None):
        self.root = root
        self.output_root = Path(output_root)
        self.modules = modules or _tk_modules()
        self.tk = self.modules["tk"]
        self.ttk = self.modules["ttk"]
        self.filedialog = self.modules["filedialog"]
        self.messagebox = self.modules["messagebox"]
        self.scrolledtext = self.modules["scrolledtext"]
        self.variables: dict[str, Any] = {}
        self.widgets: dict[str, Any] = {}
        self._running = False
        self._current_result: StandaloneRunResult | None = None
        self._current_output_dir: Path | None = None
        self._current_input: StandaloneBeamInput | None = None
        self._pending_input: StandaloneBeamInput | None = None
        self._worker_queue: queue.Queue[tuple[str, object, object | None]] = queue.Queue()
        self._suspend_form_events = False

        self._configure_root()
        self._configure_styles()
        self._build_window()
        self._load_demo_values()
        self._attach_form_traces()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_root(self) -> None:
        self.root.title(APP_TITLE)
        self.root.geometry("1080x760")
        self.root.minsize(920, 680)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

    def _configure_styles(self) -> None:
        style = self.ttk.Style(self.root)
        with_context = getattr(style, "theme_use", None)
        if with_context:
            with suppress(self.tk.TclError):
                style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8))
        style.configure("Action.TButton", padding=(9, 6))
        style.configure("Hint.TLabel", foreground="#5d6470", font=("Segoe UI", 9))
        style.configure("Danger.TLabel", foreground="#9f1d20", font=("Segoe UI", 11, "bold"))
        style.configure("Warning.TLabel", foreground="#8a5300", font=("Segoe UI", 11, "bold"))

    def _build_window(self) -> None:
        banner = self.tk.Label(
            self.root,
            text=SAFETY_BANNER,
            background="#9f1d20",
            foreground="white",
            justify="left",
            anchor="w",
            padx=18,
            pady=10,
            font=("Segoe UI", 10, "bold"),
        )
        banner.grid(row=0, column=0, sticky="ew")

        content = self.ttk.Panedwindow(self.root, orient="horizontal")
        content.grid(row=1, column=0, sticky="nsew", padx=14, pady=12)

        left_shell = self.ttk.Frame(content)
        right = self.ttk.Frame(content, padding=(14, 0, 2, 0))
        content.add(left_shell, weight=3)
        content.add(right, weight=2)
        left_shell.columnconfigure(0, weight=1)
        left_shell.rowconfigure(0, weight=1)
        self.input_canvas = self.tk.Canvas(left_shell, highlightthickness=0)
        input_scrollbar = self.ttk.Scrollbar(
            left_shell,
            orient="vertical",
            command=self.input_canvas.yview,
        )
        self.input_canvas.configure(yscrollcommand=input_scrollbar.set)
        self.input_canvas.grid(row=0, column=0, sticky="nsew")
        input_scrollbar.grid(row=0, column=1, sticky="ns")
        left = self.ttk.Frame(self.input_canvas, padding=(2, 0, 10, 8))
        self._left_canvas_window = self.input_canvas.create_window(
            (0, 0),
            window=left,
            anchor="nw",
        )
        left.bind("<Configure>", self._sync_left_scroll_region)
        self.input_canvas.bind("<Configure>", self._resize_left_content)
        self.input_canvas.bind("<Enter>", self._activate_left_scroll)
        self.input_canvas.bind("<Leave>", self._deactivate_left_scroll)
        left.columnconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(4, weight=1)

        self.ttk.Label(left, text="Исходные данные балки", style="Title.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.ttk.Label(
            left,
            text=(
                "Область: прямоугольная балка · кратковременный маршрут. "
                "Значения ниже демонстрационные, не рекомендуемые."
            ),
            style="Hint.TLabel",
            wraplength=610,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 8))

        identity = self.ttk.LabelFrame(
            left,
            text="Расчёт",
            style="Section.TLabelframe",
            padding=9,
        )
        identity.grid(row=2, column=0, sticky="ew", pady=4)
        identity.columnconfigure(1, weight=1)
        self._entry_row(identity, 0, "case_id", "Идентификатор расчёта", "")
        self.ttk.Label(
            identity,
            text="Не указывайте ФИО, email, подписи или локальные пути.",
            style="Hint.TLabel",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(3, 0))

        geometry = self.ttk.LabelFrame(
            left,
            text="Геометрия",
            style="Section.TLabelframe",
            padding=9,
        )
        geometry.grid(row=3, column=0, sticky="ew", pady=4)
        geometry.columnconfigure(1, weight=1)
        self._entry_row(geometry, 0, "b_mm", "Ширина сечения b", "мм")
        self._entry_row(geometry, 1, "h_mm", "Высота сечения h", "мм")
        self._entry_row(
            geometry,
            2,
            "cover_mm",
            "От грани бетона до наружной поверхности хомута",
            "мм",
        )
        self._combo_row(
            geometry,
            3,
            "stirrup_diameter_mm",
            "Диаметр хомута для геометрии",
            tuple(str(value) for value in STIRRUP_DIAMETERS),
            "мм",
        )

        materials = self.ttk.LabelFrame(
            left,
            text="Материалы",
            style="Section.TLabelframe",
            padding=9,
        )
        materials.grid(row=4, column=0, sticky="ew", pady=4)
        materials.columnconfigure(1, weight=1)
        self._combo_row(
            materials,
            0,
            "concrete_class",
            "Класс бетона",
            tuple(sorted(SUPPORTED_ULS_CONCRETE_CLASSES)),
        )
        self._combo_row(
            materials,
            1,
            "longitudinal_rebar_class",
            "Класс продольной арматуры",
            tuple(sorted(SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES)),
        )
        self._combo_row(
            materials,
            2,
            "stirrup_rebar_class",
            "Класс поперечной арматуры",
            tuple(sorted(REBAR_CATALOG)),
        )
        self.ttk.Label(
            materials,
            text="Текущий программный каталог требует инженерной проверки.",
            style="Hint.TLabel",
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))

        actions = self.ttk.LabelFrame(
            left,
            text="Усилия и локальная грань",
            style="Section.TLabelframe",
            padding=9,
        )
        actions.grid(row=5, column=0, sticky="ew", pady=4)
        actions.columnconfigure(1, weight=1)
        self._entry_row(actions, 0, "moment_kNm", "Модуль момента |M|", "кН·м")
        self._entry_row(actions, 1, "shear_kN", "Модуль поперечной силы |Q|", "кН")
        self._combo_row(
            actions,
            2,
            "tension_face",
            "Растянутая грань",
            ("local_y_min", "local_y_max"),
        )
        self.ttk.Label(
            actions,
            text=(
                "|M| и |Q| вводятся как неотрицательные модули; знак M не выбирает "
                "грань. Сопоставление local_y_min/local_y_max с реальным элементом "
                "должен проверить инженер."
            ),
            style="Hint.TLabel",
            wraplength=590,
            justify="left",
        ).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(4, 0))

        command_bar = self.ttk.Frame(left)
        command_bar.grid(row=6, column=0, sticky="ew", pady=(10, 2))
        command_bar.columnconfigure(0, weight=1)
        self.run_button = self.ttk.Button(
            command_bar,
            text="Выполнить исследовательскую проверку",
            style="Primary.TButton",
            command=self._start_run,
        )
        self.run_button.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 7))
        self.demo_button = self.ttk.Button(
            command_bar,
            text="Демонстрационные данные",
            style="Action.TButton",
            command=self._load_demo_values,
        )
        self.demo_button.grid(row=1, column=0, sticky="ew", padx=(0, 4))
        self.load_button = self.ttk.Button(
            command_bar,
            text="Загрузить JSON",
            style="Action.TButton",
            command=self._load_json,
        )
        self.load_button.grid(row=1, column=1, sticky="ew", padx=4)
        self.save_button = self.ttk.Button(
            command_bar,
            text="Сохранить JSON",
            style="Action.TButton",
            command=self._save_json,
        )
        self.save_button.grid(row=1, column=2, sticky="ew", padx=(4, 0))
        self.form_action_buttons = (
            self.demo_button,
            self.load_button,
            self.save_button,
        )

        self.ttk.Label(right, text="Результат", style="Title.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.result_title = self.tk.Label(
            right,
            text="Расчёт ещё не запускался",
            foreground="#5d6470",
            justify="left",
            anchor="w",
            wraplength=400,
            font=("Segoe UI", 11, "bold"),
        )
        self.result_title.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        status_frame = self.ttk.LabelFrame(
            right,
            text="Статусы",
            style="Section.TLabelframe",
            padding=10,
        )
        status_frame.grid(row=2, column=0, sticky="ew", pady=4)
        status_frame.columnconfigure(0, weight=1)
        self.status_variables = {
            name: self.tk.StringVar(value=value)
            for name, value in {
                "overall": "Общий статус: не запускался",
                "preflight": "Техническая проверка: не запускалась",
                "calculation": "Расчётный маршрут: не запускался",
                "evidence": "Инженерные подтверждения: требуются",
                "project": "Применение в проекте ЗАПРЕЩЕНО (project_use=false)",
                "review": "Требуется инженерная проверка",
            }.items()
        }
        for row, name in enumerate(
            ("overall", "preflight", "calculation", "evidence", "project", "review")
        ):
            self.ttk.Label(
                status_frame,
                textvariable=self.status_variables[name],
                wraplength=400,
                justify="left",
            ).grid(row=row, column=0, sticky="ew", pady=2)

        result_actions = self.ttk.LabelFrame(
            right,
            text="Файлы результата",
            style="Section.TLabelframe",
            padding=10,
        )
        result_actions.grid(row=3, column=0, sticky="ew", pady=4)
        result_actions.columnconfigure(0, weight=1)
        self.open_report_button = self.ttk.Button(
            result_actions,
            text="Открыть верхнеуровневый HTML-отчёт",
            command=self._open_report,
            state="disabled",
        )
        self.open_report_button.grid(row=0, column=0, sticky="ew", pady=3)
        self.open_folder_button = self.ttk.Button(
            result_actions,
            text="Открыть папку текущего результата",
            command=self._open_result_folder,
            state="disabled",
        )
        self.open_folder_button.grid(row=1, column=0, sticky="ew", pady=3)
        self.export_button = self.ttk.Button(
            result_actions,
            text="Сохранить пакет для рецензента",
            command=self._export_review_bundle,
            state="disabled",
        )
        self.export_button.grid(row=2, column=0, sticky="ew", pady=3)

        detail_frame = self.ttk.LabelFrame(
            right,
            text="Сообщения",
            style="Section.TLabelframe",
            padding=8,
        )
        detail_frame.grid(row=4, column=0, sticky="nsew", pady=4)
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(0, weight=1)
        self.details = self.scrolledtext.ScrolledText(
            detail_frame,
            height=8,
            wrap="word",
            font=("Segoe UI", 9),
            state="disabled",
        )
        self.details.grid(row=0, column=0, sticky="nsew")
        self._set_details(
            (
                "Введите или загрузите исходные данные.",
                "Выберите local_y_min или local_y_max осознанно.",
                "Итог программы не является утверждением несущей способности.",
            )
        )

        footer = self.tk.Label(
            self.root,
            text=FOOTER_TEXT,
            background="#2f3338",
            foreground="white",
            anchor="w",
            padx=16,
            pady=7,
            font=("Consolas", 9),
        )
        footer.grid(row=2, column=0, sticky="ew")

        self.root.bind("<Control-Return>", lambda _event: self._start_run())
        self.root.bind("<Control-o>", lambda _event: self._load_json())
        self.root.bind("<Control-s>", lambda _event: self._save_json())

    def _sync_left_scroll_region(self, _event: Any) -> None:
        self.input_canvas.configure(scrollregion=self.input_canvas.bbox("all"))

    def _resize_left_content(self, event: Any) -> None:
        self.input_canvas.itemconfigure(self._left_canvas_window, width=event.width)

    def _activate_left_scroll(self, _event: Any) -> None:
        self.input_canvas.bind_all("<MouseWheel>", self._scroll_left)

    def _deactivate_left_scroll(self, _event: Any) -> None:
        self.input_canvas.unbind_all("<MouseWheel>")

    def _scroll_left(self, event: Any) -> None:
        steps = -1 if event.delta > 0 else 1
        self.input_canvas.yview_scroll(steps, "units")

    def _attach_form_traces(self) -> None:
        for variable in self.variables.values():
            variable.trace_add("write", self._on_form_changed)

    def _on_form_changed(self, *_args: object) -> None:
        if self._suspend_form_events or self._running:
            return
        self._clear_result(
            "Исходные данные изменены. Выполните новую исследовательскую проверку."
        )

    def _set_form_locked(self, locked: bool) -> None:
        for field, widget in self.widgets.items():
            state = "disabled" if locked else (
                "readonly" if field in {
                    "stirrup_diameter_mm",
                    "concrete_class",
                    "longitudinal_rebar_class",
                    "stirrup_rebar_class",
                    "tension_face",
                } else "normal"
            )
            widget.configure(state=state)
        for button in self.form_action_buttons:
            button.configure(state="disabled" if locked else "normal")

    def _reset_status_variables(self) -> None:
        defaults = {
            "overall": "Общий статус: не запускался",
            "preflight": "Техническая проверка: не запускалась",
            "calculation": "Расчётный маршрут: не запускался",
            "evidence": "Инженерные подтверждения: требуются",
            "project": "Применение в проекте ЗАПРЕЩЕНО (project_use=false)",
            "review": "Требуется инженерная проверка",
        }
        for name, value in defaults.items():
            self.status_variables[name].set(value)

    def _entry_row(self, parent: Any, row: int, field: str, label: str, unit: str) -> None:
        self.ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        variable = self.tk.StringVar()
        widget = self.ttk.Entry(parent, textvariable=variable, width=24)
        widget.grid(row=row, column=1, sticky="ew", pady=3)
        self.ttk.Label(parent, text=unit, width=6).grid(row=row, column=2, sticky="w", padx=(7, 0))
        self.variables[field] = variable
        self.widgets[field] = widget

    def _combo_row(
        self,
        parent: Any,
        row: int,
        field: str,
        label: str,
        choices: tuple[str, ...],
        unit: str = "",
    ) -> None:
        self.ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        variable = self.tk.StringVar()
        widget = self.ttk.Combobox(
            parent,
            textvariable=variable,
            values=choices,
            state="readonly",
            width=22,
        )
        widget.grid(row=row, column=1, sticky="ew", pady=3)
        self.ttk.Label(parent, text=unit, width=6).grid(row=row, column=2, sticky="w", padx=(7, 0))
        self.variables[field] = variable
        self.widgets[field] = widget

    def _load_demo_values(self) -> None:
        if self._running:
            return
        self._suspend_form_events = True
        try:
            for field, value in DEMO_VALUES.items():
                self.variables[field].set(value)
        finally:
            self._suspend_form_events = False
        self._clear_result(
            "Загружены демонстрационные значения. Выберите растянутую грань перед запуском."
        )
        self.widgets["tension_face"].focus_set()

    def _form_values(self) -> dict[str, str]:
        return {field: self.variables[field].get() for field in FORM_FIELDS}

    def _start_run(self) -> None:
        if self._running:
            return
        self._clear_result("Проверка исходных данных…")
        try:
            input_data = parse_form_values(self._form_values())
        except ValueError as exc:
            self._show_input_error(str(exc))
            return

        output_dir = next_output_dir(self.output_root, input_data.case_id)
        self._running = True
        self._current_input = None
        self._pending_input = input_data
        self._set_form_locked(True)
        self.run_button.configure(state="disabled", text="Формируется диагностический пакет…")
        self.result_title.configure(text="Выполнение расчётного маршрута…", foreground="#8a5300")
        self._set_details(
            (
                "Техническая проверка данных завершена.",
                "Выполняется существующий детерминированный маршрут.",
                "Окно можно оставить открытым; повторный запуск временно заблокирован.",
            )
        )

        def worker() -> None:
            try:
                result = run_standalone_beam_case(input_data, output_dir)
            except Exception as exc:  # defensive GUI boundary; controller is fail-closed
                self._worker_queue.put(("exception", str(exc), None))
            else:
                self._worker_queue.put(("result", result, output_dir))

        threading.Thread(target=worker, name="gbk-standalone-run", daemon=True).start()
        self.root.after(75, self._poll_worker_queue)

    def _poll_worker_queue(self) -> None:
        try:
            kind, payload, output_dir = self._worker_queue.get_nowait()
        except queue.Empty:
            if self._running:
                self.root.after(75, self._poll_worker_queue)
            return
        if kind == "exception":
            self._finish_exception(str(payload))
            return
        if not isinstance(payload, StandaloneRunResult) or output_dir is None:
            self._finish_exception("Некорректный результат фонового расчётного маршрута.")
            return
        if self._pending_input is None:
            self._finish_exception("Исходные данные фонового запуска потеряны.")
            return
        self._finish_run(payload, Path(output_dir), self._pending_input)

    def _finish_exception(self, message: str) -> None:
        self._running = False
        self._set_form_locked(False)
        self.run_button.configure(state="normal", text="Выполнить исследовательскую проверку")
        self._current_result = None
        self._current_output_dir = None
        self._current_input = None
        self._pending_input = None
        self.result_title.configure(text="Расчётный маршрут не выполнен", foreground="#9f1d20")
        self._set_details(("Внутренняя ошибка оболочки.", message))
        self.messagebox.showerror(
            "ЖБК — ошибка",
            "Расчётный маршрут не выполнен. Старые ссылки на результат отключены.\n\n" + message,
            parent=self.root,
        )

    def _finish_run(
        self,
        result: StandaloneRunResult,
        output_dir: Path,
        input_data: StandaloneBeamInput,
    ) -> None:
        self._running = False
        self._set_form_locked(False)
        self._pending_input = None
        self.run_button.configure(state="normal", text="Выполнить исследовательскую проверку")
        gate_errors = verify_gui_result(result, output_dir)
        if gate_errors:
            self._current_result = None
            self._current_output_dir = None
            self._current_input = None
            self.result_title.configure(
                text="Результат заблокирован защитной проверкой",
                foreground="#9f1d20",
            )
            blocked_statuses = {
                "overall": "Защитная проверка результата: НЕ ПРОЙДЕНА",
                "preflight": "Статусы заблокированного результата не считаются доверенными",
                "calculation": "Файлы расчётного маршрута не открываются",
                "evidence": "Требуется разбор причины блокировки",
                "project": (
                    "Применение в проекте ЗАПРЕЩЕНО; целостность результата "
                    "не подтверждена"
                ),
                "review": "Требуется инженерная и техническая проверка",
            }
            for name, value in blocked_statuses.items():
                self.status_variables[name].set(value)
            self._set_details(gate_errors)
            self.messagebox.showerror(
                "ЖБК — результат заблокирован",
                "Файлы результата не открываются и не передаются:\n\n"
                + "\n".join(f"• {error}" for error in gate_errors),
                parent=self.root,
            )
            return

        view = status_view_model(result)
        self.result_title.configure(
            text=view.title,
            foreground="#8a5300" if view.tone == "warning" else "#9f1d20",
        )
        for name in ("overall", "preflight", "calculation", "evidence"):
            self.status_variables[name].set(getattr(view, name))
        self.status_variables["project"].set(view.project_use_text)
        self.status_variables["review"].set(view.review_text)
        self._set_details(view.details or (view.title,))
        self._current_result = result
        self._current_output_dir = output_dir
        self._current_input = input_data
        for button in (
            self.open_report_button,
            self.open_folder_button,
            self.export_button,
        ):
            button.configure(state="normal")

    def _clear_result(self, detail: str) -> None:
        self._current_result = None
        self._current_output_dir = None
        self._current_input = None
        for button in (
            getattr(self, "open_report_button", None),
            getattr(self, "open_folder_button", None),
            getattr(self, "export_button", None),
        ):
            if button is not None:
                button.configure(state="disabled")
        if hasattr(self, "result_title"):
            self.result_title.configure(text="Расчёт ещё не запускался", foreground="#5d6470")
        if hasattr(self, "status_variables"):
            self._reset_status_variables()
        if hasattr(self, "details"):
            self._set_details((detail,))

    def _show_input_error(self, message: str) -> None:
        self.result_title.configure(text="Исправьте исходные данные", foreground="#9f1d20")
        self._set_details((message, "Расчётный маршрут не запускался."))
        self.messagebox.showerror("ЖБК — исходные данные", message, parent=self.root)

    def _set_details(self, messages: tuple[str, ...]) -> None:
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", "\n\n".join(message for message in messages if message))
        self.details.configure(state="disabled")

    def _load_json(self) -> None:
        if self._running:
            return
        selected = self.filedialog.askopenfilename(
            parent=self.root,
            title="Открыть исходные данные ЖБК",
            filetypes=(("JSON", "*.json"), ("Все файлы", "*.*")),
        )
        if not selected:
            return
        try:
            loaded = load_standalone_input(Path(selected))
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.messagebox.showerror("ЖБК — загрузка JSON", str(exc), parent=self.root)
            return
        self._suspend_form_events = True
        try:
            for field, value in asdict(loaded).items():
                self.variables[field].set(
                    f"{value:g}" if isinstance(value, float) else str(value)
                )
        finally:
            self._suspend_form_events = False
        self._clear_result("Исходные данные загружены. Проверьте локальную грань перед запуском.")

    def _save_json(self) -> None:
        if self._running:
            return
        try:
            input_data = parse_form_values(self._form_values())
        except ValueError as exc:
            self._show_input_error(str(exc))
            return
        selected = self.filedialog.asksaveasfilename(
            parent=self.root,
            title="Сохранить исходные данные ЖБК",
            defaultextension=".json",
            initialfile="standalone_input.json",
            filetypes=(("JSON", "*.json"),),
        )
        if not selected:
            return
        try:
            Path(selected).write_text(
                json.dumps(asdict(input_data), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            self.messagebox.showerror("ЖБК — сохранение JSON", str(exc), parent=self.root)

    def _open_report(self) -> None:
        current = self._validated_current_result("Открытие отчёта заблокировано")
        if current is None:
            return
        result, _output_dir = current
        if not result.report_index_path:
            return
        try:
            opened = webbrowser.open(Path(result.report_index_path).resolve().as_uri())
        except (OSError, webbrowser.Error) as exc:
            self._show_action_error("Не удалось открыть HTML-отчёт", str(exc))
            return
        if not opened:
            self._show_action_error(
                "Не удалось открыть HTML-отчёт",
                "Браузер не подтвердил открытие файла. Используйте кнопку открытия папки.",
            )

    def _open_result_folder(self) -> None:
        current = self._validated_current_result("Открытие папки заблокировано")
        if current is None:
            return
        _result, output_dir = current
        try:
            self._open_folder(output_dir)
        except OSError as exc:
            self._show_action_error("Не удалось открыть папку результата", str(exc))

    def _export_review_bundle(self) -> None:
        current = self._validated_current_result("Экспорт заблокирован")
        if current is None:
            return
        result, _output_dir = current
        if not result.report_zip_path:
            return
        selected = self.filedialog.asksaveasfilename(
            parent=self.root,
            title="Сохранить пакет для инженерной рецензии",
            defaultextension=".zip",
            initialfile="standalone_review_bundle.zip",
            filetypes=(("ZIP", "*.zip"),),
        )
        if not selected:
            return
        destination = Path(selected)
        temporary = destination.with_name(
            f".{destination.name}.{uuid4().hex}.gbk-export.tmp"
        )
        try:
            shutil.copyfile(result.report_zip_path, temporary)
            validation_errors = verify_review_bundle(result, temporary)
            if validation_errors:
                self.messagebox.showerror(
                    "ЖБК — экспорт заблокирован",
                    "Скопированный пакет не прошёл повторную проверку:\n\n"
                    + "\n".join(f"• {error}" for error in validation_errors),
                    parent=self.root,
                )
                return
            os.replace(temporary, destination)
        except OSError as exc:
            self.messagebox.showerror("ЖБК — экспорт", str(exc), parent=self.root)
            return
        finally:
            with suppress(OSError):
                temporary.unlink()
        self.messagebox.showinfo(
            "ЖБК — пакет сохранён",
            "Сохранён только публичный пакет для инженерной рецензии.\n"
            "Он не является утверждённым проектным расчётом.",
            parent=self.root,
        )

    def _validated_current_result(
        self,
        action_title: str,
    ) -> tuple[StandaloneRunResult, Path] | None:
        result = self._current_result
        output_dir = self._current_output_dir
        expected_input = self._current_input
        if result is None or output_dir is None or expected_input is None:
            return None
        try:
            visible_input = parse_form_values(self._form_values())
        except ValueError as exc:
            self._invalidate_action(action_title, (str(exc),))
            return None
        if visible_input != expected_input:
            self._invalidate_action(
                action_title,
                (
                    "Видимые исходные данные отличаются от данных сформированного "
                    "результата.",
                ),
            )
            return None
        gate_errors = verify_gui_result(result, output_dir)
        if gate_errors:
            self._invalidate_action(action_title, gate_errors)
            return None
        return result, output_dir

    def _invalidate_action(self, title: str, errors: tuple[str, ...]) -> None:
        self._clear_result("Результат больше не проходит защитную проверку.")
        self.messagebox.showerror(
            f"ЖБК — {title}",
            "\n".join(f"• {error}" for error in errors),
            parent=self.root,
        )

    def _show_action_error(self, title: str, message: str) -> None:
        self.messagebox.showerror(
            f"ЖБК — {title}",
            message,
            parent=self.root,
        )

    def _open_folder(self, path: Path) -> None:
        resolved = Path(path).resolve()
        if sys.platform == "win32":
            os.startfile(str(resolved))  # type: ignore[attr-defined]
            return
        webbrowser.open(resolved.as_uri())

    def _on_close(self) -> None:
        if self._running:
            self.messagebox.showwarning(
                "ЖБК — выполняется расчёт",
                "Дождитесь завершения формирования диагностического пакета.",
                parent=self.root,
            )
            return
        self.root.destroy()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gbk-engineer-gui")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd() / "output" / "engineer_gui",
        help="Корневая папка отдельных запусков GUI.",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Проверить доступность Tcl/Tk без создания окна.",
    )
    parser.add_argument(
        "--headless-smoke",
        action="store_true",
        help="Создать и скрыть реальное окно для Windows CI, затем завершиться.",
    )
    parser.add_argument(
        "--exercise-run",
        action="store_true",
        help="В headless-smoke выполнить полный GUI-маршрут через очередь событий.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        modules = _tk_modules()
        if args.self_check:
            interpreter = modules["tk"].Tcl()
            patchlevel = interpreter.call("info", "patchlevel")
            print(f"tkinter_self_check=pass; tcl={patchlevel}")
            return 0

        if args.exercise_run and not args.headless_smoke:
            raise ValueError("--exercise-run требует --headless-smoke")
        root = modules["tk"].Tk()
        if args.headless_smoke:
            root.withdraw()
            modules = {**modules, "messagebox": _HeadlessMessageBox}
        app = EngineerGui(root, output_root=args.output_root, modules=modules)
        if args.headless_smoke:
            root.update_idletasks()
            parse_form_values({**DEMO_VALUES, "tension_face": "local_y_min"})
            if len(app.widgets) != len(FORM_FIELDS):
                raise RuntimeError("GUI field count does not match standalone contract")
            if args.exercise_run:
                app.variables["tension_face"].set("local_y_min")
                app._start_run()
                deadline = time.monotonic() + 60.0
                while app._running and time.monotonic() < deadline:
                    root.update()
                    time.sleep(0.01)
                root.update()
                if app._running:
                    raise TimeoutError("GUI calculation smoke exceeded 60 seconds")
                if app._current_result is None or app._current_output_dir is None:
                    raise RuntimeError("GUI calculation smoke did not expose a safe result")
            root.destroy()
            mode = "calculation" if args.exercise_run else "window"
            print(f"engineer_gui_headless_smoke=pass; mode={mode}")
            return 0
        root.mainloop()
        return 0
    except Exception as exc:
        _record_startup_error(exc)
        if not args.headless_smoke:
            _show_startup_error(exc)
        print(f"ОШИБКА ЗАПУСКА ИНТЕРФЕЙСА: {exc}", file=sys.stderr)
        return 2


def _record_startup_error(exc: Exception) -> None:
    with suppress(OSError):
        (Path.cwd() / "GUI_LAUNCH_LOG.txt").write_text(
            "GBK engineer GUI startup failed.\n" + f"{type(exc).__name__}: {exc}\n",
            encoding="utf-8",
        )


def _show_startup_error(exc: Exception) -> None:
    """Best-effort visible error for pythonw launches without a console."""
    try:
        modules = _tk_modules()
        error_root = modules["tk"].Tk()
        error_root.withdraw()
        modules["messagebox"].showerror(
            "ЖБК — интерфейс не запущен",
            "Инженерный интерфейс не удалось открыть.\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            "Подробности сохранены в GUI_LAUNCH_LOG.txt.",
            parent=error_root,
        )
        error_root.destroy()
    except Exception:
        return


if __name__ == "__main__":
    raise SystemExit(main())
