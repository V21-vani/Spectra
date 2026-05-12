import threading
import csv
import json
import io
import base64
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import flet as ft
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.models import TestResult
from src.parser import parse_junit_xml
from src.runner import run_pytest
from src import storage

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = "#0d0d1a"
SURFACE  = "#13132b"
SURFACE2 = "#1a1a3a"
BORDER   = "#2a2a50"
ACCENT   = "#7c6af7"
GREEN    = "#4ade80"
RED      = "#f87171"
YELLOW   = "#fbbf24"
ORANGE   = "#fb923c"
BLUE     = "#60a5fa"
TEAL     = "#2dd4bf"
TEXT     = "#e2e8f0"
SUBTEXT  = "#7c8aac"

S_COLOR = {"PASSED": GREEN, "FAILED": RED, "SKIPPED": YELLOW, "ERROR": ORANGE}
S_ICON  = {
    "PASSED": ft.Icons.CHECK_CIRCLE,
    "FAILED": ft.Icons.CANCEL,
    "SKIPPED": ft.Icons.SKIP_NEXT,
    "ERROR":  ft.Icons.ERROR,
}

# ── Chart helpers ──────────────────────────────────────────────────────────────
def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=SURFACE, dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def make_pie(results: list[TestResult]) -> str:
    counts = {s: sum(1 for r in results if r.status == s)
              for s in ["PASSED", "FAILED", "SKIPPED", "ERROR"]}
    counts = {k: v for k, v in counts.items() if v > 0}
    if not counts:
        return ""
    fig, ax = plt.subplots(figsize=(3.8, 3))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    wedges, texts, autos = ax.pie(
        counts.values(),
        labels=counts.keys(),
        colors=[S_COLOR[s] for s in counts],
        autopct="%1.0f%%",
        startangle=90,
        textprops={"color": TEXT, "fontsize": 9},
        wedgeprops={"linewidth": 1.5, "edgecolor": SURFACE},
    )
    for at in autos:
        at.set_color(BG)
        at.set_fontsize(8)
        at.set_fontweight("bold")
    return _fig_to_b64(fig)


def make_duration_bar(results: list[TestResult]) -> str:
    if not results:
        return ""
    top = sorted(results, key=lambda r: r.duration, reverse=True)[:12]
    names = [
        (r.test_name[:22] + "…") if len(r.test_name) > 23 else r.test_name
        for r in top
    ]
    fig, ax = plt.subplots(figsize=(5, 3))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.barh(names, [r.duration for r in top],
            color=[S_COLOR[r.status] for r in top], alpha=0.85, height=0.6)
    ax.set_xlabel("Duration (ms)", color=SUBTEXT, fontsize=8)
    ax.tick_params(colors=TEXT, labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.xaxis.label.set_color(SUBTEXT)
    ax.invert_yaxis()
    plt.tight_layout()
    return _fig_to_b64(fig)


def make_trend_bar(results: list[TestResult]) -> str:
    """Grouped bar chart: pass/fail/skip count per file."""
    if not results:
        return ""
    file_data: dict[str, dict] = defaultdict(
        lambda: {"PASSED": 0, "FAILED": 0, "SKIPPED": 0, "ERROR": 0}
    )
    for r in results:
        file_data[Path(r.test_file).name][r.status] += 1

    files = list(file_data.keys())[:10]
    x = range(len(files))
    passed  = [file_data[f]["PASSED"]  for f in files]
    failed  = [file_data[f]["FAILED"]  for f in files]
    skipped = [file_data[f]["SKIPPED"] for f in files]

    fig, ax = plt.subplots(figsize=(5, 3))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    w = 0.25
    ax.bar([i - w for i in x], passed,  width=w, color=GREEN,  alpha=0.85, label="Passed")
    ax.bar(list(x),            failed,  width=w, color=RED,    alpha=0.85, label="Failed")
    ax.bar([i + w for i in x], skipped, width=w, color=YELLOW, alpha=0.85, label="Skipped")
    ax.set_xticks(list(x))
    ax.set_xticklabels(
        [(f[:12] + "…") if len(f) > 13 else f for f in files],
        rotation=30, ha="right", fontsize=7, color=TEXT,
    )
    ax.tick_params(colors=TEXT, labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.legend(fontsize=7, facecolor=SURFACE2, labelcolor=TEXT, edgecolor=BORDER)
    plt.tight_layout()
    return _fig_to_b64(fig)


def make_coverage_bar(results: list[TestResult]) -> str:
    """Horizontal bar: average coverage % per file (only shown when coverage data exists)."""
    if not results or not any(r.coverage > 0 for r in results):
        return ""
    file_cov: dict[str, list] = defaultdict(list)
    for r in results:
        if r.coverage > 0:
            file_cov[Path(r.test_file).name].append(r.coverage)
    if not file_cov:
        return ""
    files = list(file_cov.keys())[:10]
    avgs  = [sum(file_cov[f]) / len(file_cov[f]) for f in files]
    colors = [GREEN if c >= 80 else (YELLOW if c >= 50 else RED) for c in avgs]

    fig, ax = plt.subplots(figsize=(5, 3))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.barh(files, avgs, color=colors, alpha=0.85, height=0.6)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Coverage %", color=SUBTEXT, fontsize=8)
    ax.axvline(80, color=ACCENT, linestyle="--", alpha=0.5, linewidth=1)
    ax.tick_params(colors=TEXT, labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.xaxis.label.set_color(SUBTEXT)
    ax.invert_yaxis()
    plt.tight_layout()
    return _fig_to_b64(fig)


# ── Widget helpers ─────────────────────────────────────────────────────────────
def card(content, expand=False, padding=16):
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=SURFACE,
        border_radius=14,
        border=ft.border.all(1, BORDER),
        expand=expand,
        shadow=ft.BoxShadow(
            blur_radius=12, spread_radius=0,
            color="#00000060", offset=ft.Offset(0, 4),
        ),
    )


def stat_card(label, value, color, icon):
    return ft.Container(
        content=ft.Column([
            ft.Icon(icon, color=color, size=20),
            ft.Text(str(value), size=34, weight=ft.FontWeight.BOLD, color=color,
                    text_align=ft.TextAlign.CENTER),
            ft.Text(label, size=11, color=SUBTEXT, text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4, tight=True),
        padding=ft.padding.symmetric(vertical=20, horizontal=12),
        bgcolor=SURFACE,
        border_radius=14,
        border=ft.border.all(1, color + "55"),
        expand=True,
        shadow=ft.BoxShadow(blur_radius=10, spread_radius=0,
                             color="#00000040", offset=ft.Offset(0, 3)),
    )


def section_title(text):
    return ft.Text(text, size=15, weight=ft.FontWeight.BOLD, color=TEXT)


def status_badge(status: str):
    color = S_COLOR.get(status, SUBTEXT)
    return ft.Container(
        content=ft.Text(status, size=10, color=color, weight=ft.FontWeight.BOLD),
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        border_radius=20,
        bgcolor=color + "22",
        border=ft.border.all(1, color + "66"),
    )


# ── Main app ───────────────────────────────────────────────────────────────────
def main(page: ft.Page):
    page.title = "Spectra — Test Analytics"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.window.width = 1340
    page.window.height = 860
    page.window.min_width = 960
    page.window.min_height = 620
    page.fonts = {"mono": "Courier New"}

    # ── Shared state ──────────────────────────────────────────────────────────
    test_results: list[TestResult] = []
    current_view = [0]

    # Results-view filter/sort state — persists across navigations
    _filter_status = [None]
    _filter_file   = [None]
    _search_q      = [""]
    _sort_col      = [None]   # int column index or None
    _sort_asc      = [True]

    # ── File pickers — created once to avoid overlay accumulation ─────────────
    xml_picker      = ft.FilePicker()
    json_imp_picker = ft.FilePicker()
    dir_picker      = ft.FilePicker()
    page.overlay.extend([xml_picker, json_imp_picker, dir_picker])

    # ── Content container ─────────────────────────────────────────────────────
    content_area = ft.Container(expand=True, padding=24, bgcolor=BG)

    # ── Snackbar helper ───────────────────────────────────────────────────────
    def snack(msg: str, color=GREEN):
        page.snack_bar = ft.SnackBar(
            ft.Text(msg, color=BG, weight=ft.FontWeight.BOLD),
            bgcolor=color, duration=2500,
        )
        page.snack_bar.open = True
        page.update()

    # ═══════════════════════════════════════════════════════════════════════════
    # DASHBOARD VIEW
    # ═══════════════════════════════════════════════════════════════════════════
    def build_dashboard():
        total   = len(test_results)
        passed  = sum(1 for r in test_results if r.status == "PASSED")
        failed  = sum(1 for r in test_results if r.status == "FAILED")
        skipped = sum(1 for r in test_results if r.status == "SKIPPED")
        errors  = sum(1 for r in test_results if r.status == "ERROR")
        pass_rate     = (passed / total * 100) if total else 0
        avg_dur       = sum(r.duration for r in test_results) / total if total else 0
        avg_cov       = sum(r.coverage for r in test_results) / total if total else 0
        total_runtime = sum(r.duration for r in test_results)
        has_coverage  = any(r.coverage > 0 for r in test_results)

        if total_runtime >= 60_000:
            runtime_str = f"{total_runtime / 60_000:.1f}m"
        elif total_runtime >= 1_000:
            runtime_str = f"{total_runtime / 1_000:.2f}s"
        else:
            runtime_str = f"{total_runtime:.0f}ms"

        # per-file table data
        file_stats: dict[str, dict] = {}
        for r in test_results:
            k = r.test_file
            if k not in file_stats:
                file_stats[k] = {"total": 0, "passed": 0, "failed": 0}
            file_stats[k]["total"] += 1
            if r.status == "PASSED":
                file_stats[k]["passed"] += 1
            elif r.status in ("FAILED", "ERROR"):
                file_stats[k]["failed"] += 1

        file_rows = []
        for fname, s in list(file_stats.items())[:10]:
            rate = s["passed"] / s["total"] * 100
            col  = GREEN if rate == 100 else (RED if rate < 50 else YELLOW)
            file_rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(Path(fname).name, color=TEXT, size=12,
                                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)),
                ft.DataCell(ft.Text(str(s["total"]),  color=SUBTEXT, size=12)),
                ft.DataCell(ft.Text(str(s["failed"]),
                                    color=RED if s["failed"] else SUBTEXT, size=12)),
                ft.DataCell(ft.Text(f"{rate:.0f}%", color=col, size=12,
                                    weight=ft.FontWeight.BOLD)),
            ]))

        empty_row = [ft.DataRow(cells=[
            ft.DataCell(ft.Text("No data loaded — import XML or run pytest",
                                color=SUBTEXT, size=12)),
            ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")),
        ])]

        pie_b64   = make_pie(test_results)
        dur_b64   = make_duration_bar(test_results)
        trend_b64 = make_trend_bar(test_results)
        cov_b64   = make_coverage_bar(test_results)

        cov_label = (
            f"Avg Coverage: {avg_cov:.1f}%"
            if has_coverage
            else "Coverage: not collected (enable in Run view)"
        )

        # Second chart row is only rendered when there's data
        second_charts = []
        if trend_b64:
            second_charts.append(card(ft.Column([
                section_title("Pass / Fail by File"),
                ft.Image(src_base64=trend_b64, width=460, height=270,
                         fit=ft.ImageFit.CONTAIN),
            ], spacing=10), expand=True))
        if cov_b64:
            second_charts.append(card(ft.Column([
                section_title("Coverage by File"),
                ft.Image(src_base64=cov_b64, width=460, height=270,
                         fit=ft.ImageFit.CONTAIN),
            ], spacing=10), expand=True))

        def refresh_dashboard(e):
            navigate(0)

        children = [
            ft.Row([
                ft.Column([
                    ft.Text("Dashboard", size=26, weight=ft.FontWeight.BOLD, color=TEXT),
                    ft.Text(f"Updated {datetime.now().strftime('%H:%M:%S')}",
                            size=11, color=SUBTEXT),
                ], spacing=2, expand=True),
                ft.IconButton(ft.Icons.REFRESH, icon_color=SUBTEXT, tooltip="Refresh",
                              on_click=refresh_dashboard),
            ]),
            ft.Divider(height=1, color=BORDER),

            # 6 stat cards
            ft.Row([
                stat_card("Passed",     passed,             GREEN,  ft.Icons.CHECK_CIRCLE),
                stat_card("Failed",     failed,             RED,    ft.Icons.CANCEL),
                stat_card("Skipped",    skipped,            YELLOW, ft.Icons.SKIP_NEXT),
                stat_card("Errors",     errors,             ORANGE, ft.Icons.ERROR_OUTLINE),
                stat_card("Pass Rate",  f"{pass_rate:.1f}%",BLUE,   ft.Icons.TRENDING_UP),
                stat_card("Total Time", runtime_str,        TEAL,   ft.Icons.TIMER),
            ], spacing=12),

            ft.Row([
                ft.Text(f"Total: {total}", color=SUBTEXT, size=12),
                ft.Text("·", color=BORDER, size=12),
                ft.Text(f"Avg Duration: {avg_dur:.1f} ms", color=SUBTEXT, size=12),
                ft.Text("·", color=BORDER, size=12),
                ft.Text(cov_label, color=SUBTEXT, size=12),
            ], spacing=8),

            # First chart row: status pie + slowest tests
            ft.Row([
                card(ft.Column([
                    section_title("Status Distribution"),
                    ft.Image(src_base64=pie_b64, width=360, height=270,
                             fit=ft.ImageFit.CONTAIN)
                    if pie_b64 else ft.Text("No data yet", color=SUBTEXT, size=13),
                ], spacing=10), expand=True),

                card(ft.Column([
                    section_title("Slowest Tests"),
                    ft.Image(src_base64=dur_b64, width=460, height=270,
                             fit=ft.ImageFit.CONTAIN)
                    if dur_b64 else ft.Text("No data yet", color=SUBTEXT, size=13),
                ], spacing=10), expand=True),
            ], spacing=14),
        ]

        # Second chart row (trend + coverage) — only when data exists
        if second_charts:
            children.append(ft.Row(second_charts, spacing=14))

        # Per-file breakdown table
        children.append(card(ft.Column([
            section_title("Per-File Breakdown"),
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("File",      color=SUBTEXT, size=12)),
                    ft.DataColumn(ft.Text("Total",     color=SUBTEXT, size=12), numeric=True),
                    ft.DataColumn(ft.Text("Failed",    color=SUBTEXT, size=12), numeric=True),
                    ft.DataColumn(ft.Text("Pass Rate", color=SUBTEXT, size=12), numeric=True),
                ],
                rows=file_rows or empty_row,
                border=ft.border.all(1, BORDER),
                border_radius=10,
                horizontal_lines=ft.border.BorderSide(0.5, BORDER),
                data_row_min_height=36,
            ),
        ], spacing=12)))

        return ft.Column(children, spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # RESULTS VIEW
    # ═══════════════════════════════════════════════════════════════════════════
    def build_results():

        def filtered():
            q  = _search_q[0].lower()
            st = _filter_status[0]
            ff = _filter_file[0]
            return [
                r for r in test_results
                if (not st or r.status == st)
                and (not ff or ff == "ALL" or Path(r.test_file).name == ff)
                and (not q or q in r.test_name.lower() or q in r.test_file.lower())
            ]

        _SORT_KEYS = {
            0: lambda r: r.test_file.lower(),
            1: lambda r: r.test_name.lower(),
            2: lambda r: r.status,
            3: lambda r: r.duration,
            4: lambda r: r.coverage,
        }

        def filtered_sorted():
            rows = filtered()
            col = _sort_col[0]
            if col is not None and col in _SORT_KEYS:
                rows = sorted(rows, key=_SORT_KEYS[col], reverse=not _sort_asc[0])
            return rows

        # data_table is assigned below; on_col_sort captures it via closure
        data_table = None

        def on_col_sort(e):
            _sort_col[0] = e.column_index
            _sort_asc[0] = e.ascending
            if data_table is not None:
                data_table.sort_column_index = e.column_index
                data_table.sort_ascending = e.ascending
            refresh_table()

        def make_row(r: TestResult):
            def delete(e, rid=r.id):
                test_results[:] = [x for x in test_results if x.id != rid]
                refresh_table()
                snack("Test removed", RED)

            cov_val = r.coverage
            if cov_val > 0:
                cov_color = GREEN if cov_val >= 80 else (YELLOW if cov_val >= 50 else RED)
                cov_text  = f"{cov_val:.0f}%"
            else:
                cov_color = SUBTEXT
                cov_text  = "—"

            return ft.DataRow(cells=[
                ft.DataCell(ft.Text(Path(r.test_file).name, color=TEXT, size=12,
                                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
                                    tooltip=r.test_file)),
                ft.DataCell(ft.Text(r.test_name, color=TEXT, size=12,
                                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
                                    tooltip=r.test_name)),
                ft.DataCell(status_badge(r.status)),
                ft.DataCell(ft.Text(f"{r.duration:.1f}", color=SUBTEXT, size=12)),
                ft.DataCell(ft.Text(cov_text, color=cov_color, size=12)),
                ft.DataCell(
                    ft.Text(r.error_message or "—",
                            color=RED if r.error_message else SUBTEXT,
                            size=11, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
                            tooltip=r.error_message or "")
                ),
                ft.DataCell(
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=RED,
                                  icon_size=16, tooltip="Remove", on_click=delete)
                ),
            ])

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("File",   color=SUBTEXT, size=12), on_sort=on_col_sort),
                ft.DataColumn(ft.Text("Test",   color=SUBTEXT, size=12), on_sort=on_col_sort),
                ft.DataColumn(ft.Text("Status", color=SUBTEXT, size=12), on_sort=on_col_sort),
                ft.DataColumn(ft.Text("ms",     color=SUBTEXT, size=12),
                              numeric=True, on_sort=on_col_sort),
                ft.DataColumn(ft.Text("Cov %",  color=SUBTEXT, size=12),
                              numeric=True, on_sort=on_col_sort),
                ft.DataColumn(ft.Text("Error",  color=SUBTEXT, size=12)),
                ft.DataColumn(ft.Text("",       color=SUBTEXT, size=12)),
            ],
            rows=[],
            sort_column_index=_sort_col[0],
            sort_ascending=_sort_asc[0],
            border=ft.border.all(1, BORDER),
            border_radius=10,
            horizontal_lines=ft.border.BorderSide(0.5, BORDER),
            data_row_min_height=38,
            column_spacing=20,
        )

        count_text   = ft.Text("", color=SUBTEXT, size=12)
        file_filter_dd = ft.Dropdown(
            hint_text="All files", width=180, height=40,
            bgcolor=SURFACE2, border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT, hint_style=ft.TextStyle(color=SUBTEXT),
            options=[ft.dropdown.Option("ALL")],
            value="ALL" if not _filter_file[0] else _filter_file[0],
            on_change=lambda e: (
                _filter_file.__setitem__(0, None if e.control.value == "ALL" else e.control.value),
                refresh_table(),
            ),
        )

        def refresh_table():
            unique_files = sorted({Path(r.test_file).name for r in test_results})
            file_filter_dd.options = [ft.dropdown.Option("ALL")] + [
                ft.dropdown.Option(f) for f in unique_files
            ]
            if _filter_file[0] not in (None, "ALL") and _filter_file[0] not in unique_files:
                _filter_file[0] = None
                file_filter_dd.value = "ALL"

            rows = filtered_sorted()
            data_table.rows = [make_row(r) for r in rows]
            count_text.value = f"{len(rows)} result{'s' if len(rows) != 1 else ''}"
            page.update()

        # ── Add-test form ──────────────────────────────────────────────────────
        tf_file   = ft.TextField(label="Test File",      width=200, height=48,
                                  bgcolor=SURFACE2, border_color=BORDER,
                                  focused_border_color=ACCENT, color=TEXT,
                                  label_style=ft.TextStyle(color=SUBTEXT))
        tf_name   = ft.TextField(label="Test Name",      width=220, height=48,
                                  bgcolor=SURFACE2, border_color=BORDER,
                                  focused_border_color=ACCENT, color=TEXT,
                                  label_style=ft.TextStyle(color=SUBTEXT))
        dd_status = ft.Dropdown(label="Status", width=130, height=48,
                                 bgcolor=SURFACE2, border_color=BORDER,
                                 focused_border_color=ACCENT, color=TEXT,
                                 label_style=ft.TextStyle(color=SUBTEXT),
                                 options=[ft.dropdown.Option(s)
                                          for s in ["PASSED", "FAILED", "SKIPPED", "ERROR"]],
                                 value="PASSED")
        tf_dur    = ft.TextField(label="Duration (ms)", width=130, height=48,
                                  bgcolor=SURFACE2, border_color=BORDER,
                                  focused_border_color=ACCENT, color=TEXT,
                                  label_style=ft.TextStyle(color=SUBTEXT),
                                  keyboard_type=ft.KeyboardType.NUMBER, value="0")
        tf_cov    = ft.TextField(label="Coverage %",   width=120, height=48,
                                  bgcolor=SURFACE2, border_color=BORDER,
                                  focused_border_color=ACCENT, color=TEXT,
                                  label_style=ft.TextStyle(color=SUBTEXT),
                                  keyboard_type=ft.KeyboardType.NUMBER, value="0")
        add_err   = ft.Text("", color=RED, size=12)

        def add_test(e):
            try:
                file = tf_file.value.strip()
                name = tf_name.value.strip()
                if not file:
                    raise ValueError("Test file required")
                if not name:
                    raise ValueError("Test name required")
                dur = float(tf_dur.value or 0)
                cov = float(tf_cov.value or 0)
                if not (0 <= cov <= 100):
                    raise ValueError("Coverage must be 0–100")
                if any(r.test_file == file and r.test_name == name for r in test_results):
                    raise ValueError(f"Duplicate: '{name}' in '{file}' already exists")
                test_results.append(TestResult(
                    test_file=file, test_name=name,
                    status=dd_status.value, duration=dur, coverage=cov,
                ))
                tf_file.value = tf_name.value = ""
                tf_dur.value = tf_cov.value = "0"
                add_err.value = ""
                refresh_table()
                snack(f"Added '{name}'")
            except ValueError as ex:
                add_err.value = str(ex)
                page.update()

        def clear_all(e):
            test_results.clear()
            refresh_table()
            snack("Cleared all results", ORANGE)

        # ── XML import ─────────────────────────────────────────────────────────
        def on_xml_pick(e: ft.FilePickerResultEvent):
            if not e.files:
                return
            results, err = parse_junit_xml(e.files[0].path)
            if err:
                snack(f"Import error: {err}", RED)
                return
            test_results.clear()
            test_results.extend(results)
            refresh_table()
            snack(f"Imported {len(results)} tests from {Path(e.files[0].path).name}")

        xml_picker.on_result = on_xml_pick

        # ── JSON import ────────────────────────────────────────────────────────
        def on_json_pick(e: ft.FilePickerResultEvent):
            if not e.files:
                return
            try:
                with open(e.files[0].path, encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Expected a JSON array at root")
                loaded = [TestResult(**item) for item in data]
                test_results.clear()
                test_results.extend(loaded)
                refresh_table()
                snack(f"Imported {len(loaded)} tests from {Path(e.files[0].path).name}")
            except Exception as ex:
                snack(f"Import error: {ex}", RED)

        json_imp_picker.on_result = on_json_pick

        # ── Export ─────────────────────────────────────────────────────────────
        def export_csv(e):
            if not test_results:
                snack("Nothing to export", ORANGE)
                return
            path = os.path.join(os.path.expanduser("~"), "Desktop", "spectra_export.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["test_file", "test_name", "status",
                             "duration_ms", "coverage_pct", "error"])
                for r in test_results:
                    w.writerow([r.test_file, r.test_name, r.status,
                                r.duration, r.coverage, r.error_message or ""])
            snack(f"Exported to {path}")

        def export_json(e):
            if not test_results:
                snack("Nothing to export", ORANGE)
                return
            from dataclasses import asdict
            path = os.path.join(os.path.expanduser("~"), "Desktop", "spectra_export.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in test_results], f, indent=2)
            snack(f"Exported to {path}")

        # ── Filter bar ─────────────────────────────────────────────────────────
        search_field = ft.TextField(
            hint_text="Search tests…", width=240, height=40,
            bgcolor=SURFACE2, border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT, hint_style=ft.TextStyle(color=SUBTEXT),
            prefix_icon=ft.Icons.SEARCH, value=_search_q[0],
            on_change=lambda e: (_search_q.__setitem__(0, e.control.value), refresh_table()),
        )
        status_filter_dd = ft.Dropdown(
            hint_text="All statuses", width=150, height=40,
            bgcolor=SURFACE2, border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT, hint_style=ft.TextStyle(color=SUBTEXT),
            options=[ft.dropdown.Option("ALL")] +
                    [ft.dropdown.Option(s) for s in ["PASSED", "FAILED", "SKIPPED", "ERROR"]],
            value="ALL" if not _filter_status[0] else _filter_status[0],
            on_change=lambda e: (
                _filter_status.__setitem__(0,
                    None if e.control.value == "ALL" else e.control.value),
                refresh_table(),
            ),
        )

        refresh_table()

        return ft.Column([
            ft.Row([
                ft.Text("Results", size=26, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.Container(expand=True),
                ft.FilledButton(
                    "Import XML", icon=ft.Icons.UPLOAD_FILE,
                    on_click=lambda e: xml_picker.pick_files(allowed_extensions=["xml"]),
                    style=ft.ButtonStyle(bgcolor=ACCENT)),
                ft.FilledButton(
                    "Import JSON", icon=ft.Icons.FILE_OPEN,
                    on_click=lambda e: json_imp_picker.pick_files(allowed_extensions=["json"]),
                    style=ft.ButtonStyle(bgcolor=SURFACE2)),
                ft.FilledButton(
                    "Export CSV", icon=ft.Icons.DOWNLOAD,
                    on_click=export_csv,
                    style=ft.ButtonStyle(bgcolor=SURFACE2)),
                ft.FilledButton(
                    "Export JSON", icon=ft.Icons.CODE,
                    on_click=export_json,
                    style=ft.ButtonStyle(bgcolor=SURFACE2)),
                ft.OutlinedButton(
                    "Clear All", icon=ft.Icons.DELETE_SWEEP,
                    on_click=clear_all,
                    style=ft.ButtonStyle(color=RED, side=ft.BorderSide(1, RED))),
            ], spacing=10),
            ft.Divider(height=1, color=BORDER),

            # Manual add form
            card(ft.Column([
                section_title("Add Test Manually"),
                ft.Row([tf_file, tf_name, dd_status, tf_dur, tf_cov,
                        ft.FilledButton("Add", icon=ft.Icons.ADD, on_click=add_test,
                                        style=ft.ButtonStyle(bgcolor=ACCENT))],
                       spacing=10, wrap=True),
                add_err,
            ], spacing=10), padding=14),

            # Filter bar — click column headers in the table below to sort
            ft.Row([search_field, status_filter_dd, file_filter_dd,
                    ft.Container(expand=True), count_text], spacing=12),

            ft.Container(
                content=ft.Column([data_table], scroll=ft.ScrollMode.AUTO),
                expand=True,
                bgcolor=SURFACE,
                border_radius=14,
                border=ft.border.all(1, BORDER),
                padding=4,
            ),
        ], spacing=14, expand=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # RUN TESTS VIEW
    # ═══════════════════════════════════════════════════════════════════════════
    def build_runner():
        path_field = ft.TextField(
            label="Project / folder path", expand=True, height=48,
            bgcolor=SURFACE2, border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT, label_style=ft.TextStyle(color=SUBTEXT),
            hint_text=r"e.g. C:\Users\you\myproject",
        )
        log_area = ft.TextField(
            multiline=True, read_only=True, expand=True,
            min_lines=18, max_lines=18,
            bgcolor="#080814", border_color=BORDER, color="#aaffaa",
            text_style=ft.TextStyle(font_family="mono", size=12),
            value="",
        )
        status_text = ft.Text("Ready", color=SUBTEXT, size=13)
        cov_check   = ft.Checkbox(
            label="Enable coverage  (requires pytest-cov)",
            value=False,
            fill_color=ACCENT,
            check_color=BG,
            label_style=ft.TextStyle(color=TEXT, size=13),
        )
        run_btn  = ft.FilledButton("Run pytest", icon=ft.Icons.PLAY_ARROW,
                                    style=ft.ButtonStyle(bgcolor=GREEN))
        load_btn = ft.FilledButton("Load into Results", icon=ft.Icons.UPLOAD,
                                    style=ft.ButtonStyle(bgcolor=ACCENT),
                                    visible=False)

        last_results: list[TestResult] = []

        def on_dir_pick(e: ft.FilePickerResultEvent):
            if e.path:
                path_field.value = e.path
                page.update()

        dir_picker.on_result = on_dir_pick

        def do_run(e):
            path = path_field.value.strip()
            if not path:
                snack("Enter a path first", ORANGE)
                return
            if not os.path.exists(path):
                snack("Path does not exist", RED)
                return

            run_btn.disabled = True
            load_btn.visible = False
            log_area.value   = ""
            status_text.value = "⏳  Running…"
            status_text.color = YELLOW
            last_results.clear()
            page.update()

            use_cov = cov_check.value

            def worker():
                lines = []

                def on_line(line):
                    lines.append(line)
                    log_area.value = "".join(lines)
                    page.update()

                results, _, err = run_pytest(path, on_line=on_line, coverage=use_cov)
                last_results.extend(results)

                if err:
                    status_text.value = f"⚠  {err}"
                    status_text.color  = ORANGE
                else:
                    p = sum(1 for r in results if r.status == "PASSED")
                    f = sum(1 for r in results if r.status == "FAILED")
                    cov_note = ""
                    if use_cov and results and any(r.coverage > 0 for r in results):
                        avg = sum(r.coverage for r in results) / len(results)
                        cov_note = f" | avg cov {avg:.1f}%"
                    status_text.value = (
                        f"✓  Done — {len(results)} tests "
                        f"| {p} passed | {f} failed{cov_note}"
                    )
                    status_text.color = GREEN if f == 0 else RED

                run_btn.disabled = False
                load_btn.visible = bool(results)
                page.update()

            threading.Thread(target=worker, daemon=True).start()

        def load_results(e):
            test_results.clear()
            test_results.extend(last_results)
            snack(f"Loaded {len(last_results)} tests into Results")
            navigate(1)

        run_btn.on_click  = do_run
        load_btn.on_click = load_results

        return ft.Column([
            ft.Text("Run Tests", size=26, weight=ft.FontWeight.BOLD, color=TEXT),
            ft.Divider(height=1, color=BORDER),

            card(ft.Column([
                section_title("Target"),
                ft.Row([
                    path_field,
                    ft.IconButton(ft.Icons.FOLDER_OPEN, icon_color=ACCENT, tooltip="Browse",
                                  on_click=lambda e: dir_picker.get_directory_path()),
                    run_btn,
                    load_btn,
                ], spacing=10),
                ft.Row([cov_check, ft.Container(expand=True), status_text], spacing=12),
            ], spacing=12), padding=16),

            card(ft.Column([
                section_title("Output"),
                log_area,
            ], spacing=10), expand=True, padding=14),
        ], spacing=14, expand=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # HISTORY VIEW
    # ═══════════════════════════════════════════════════════════════════════════
    def build_history():
        sessions_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        name_field = ft.TextField(
            label="Session name", width=300, height=48,
            bgcolor=SURFACE2, border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT, label_style=ft.TextStyle(color=SUBTEXT),
            hint_text="e.g. Sprint 12 – auth tests",
        )

        def refresh_sessions():
            sessions_col.controls.clear()
            sessions = storage.load_sessions()
            if not sessions:
                sessions_col.controls.append(
                    ft.Text("No saved sessions yet — run tests or import XML, then save.",
                            color=SUBTEXT, size=13)
                )
                page.update()
                return

            for s in sessions:
                ts     = datetime.fromtimestamp(s.get("timestamp", 0)).strftime("%d %b %Y  %H:%M")
                res    = s.get("results", [])
                total  = len(res)
                passed = sum(1 for r in res if r.get("status") == "PASSED")
                failed = sum(1 for r in res if r.get("status") == "FAILED")
                fname  = s.get("_file", "")

                def load_session(e, sdata=s):
                    test_results.clear()
                    test_results.extend(storage.results_from_session(sdata))
                    snack(f"Loaded '{sdata['name']}'")
                    navigate(1)

                def del_session(e, fn=fname):
                    storage.delete_session(fn)
                    refresh_sessions()
                    snack("Session deleted", RED)

                rate_color = (GREEN if total and failed == 0
                              else RED if failed > total // 2
                              else YELLOW)

                sessions_col.controls.append(card(ft.Row([
                    ft.Column([
                        ft.Text(s.get("name", "Unnamed"), size=14,
                                weight=ft.FontWeight.BOLD, color=TEXT),
                        ft.Text(ts, size=11, color=SUBTEXT),
                    ], spacing=2, expand=True),
                    ft.Row([
                        ft.Text(f"{total} tests",  color=SUBTEXT, size=12),
                        ft.Text(f"{passed} passed", color=GREEN,  size=12),
                        ft.Text(f"{failed} failed",
                                color=RED if failed else SUBTEXT, size=12),
                        ft.Text(
                            f"{passed/total*100:.0f}%" if total else "—",
                            color=rate_color, size=13, weight=ft.FontWeight.BOLD,
                        ),
                    ], spacing=16),
                    ft.Row([
                        ft.FilledButton("Load", icon=ft.Icons.UPLOAD,
                                        on_click=load_session,
                                        style=ft.ButtonStyle(bgcolor=ACCENT)),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=RED,
                                      tooltip="Delete", on_click=del_session),
                    ], spacing=6),
                ], spacing=20, alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=14))

            page.update()

        def save_session(e):
            if not test_results:
                snack("No results to save", ORANGE)
                return
            name = (name_field.value.strip()
                    or f"Session {datetime.now().strftime('%d %b %H:%M')}")
            storage.save_session(name, test_results)
            name_field.value = ""
            refresh_sessions()
            snack(f"Saved '{name}'")

        refresh_sessions()

        return ft.Column([
            ft.Text("History", size=26, weight=ft.FontWeight.BOLD, color=TEXT),
            ft.Divider(height=1, color=BORDER),

            card(ft.Row([
                name_field,
                ft.FilledButton("Save Current Results", icon=ft.Icons.SAVE,
                                on_click=save_session,
                                style=ft.ButtonStyle(bgcolor=ACCENT)),
            ], spacing=12), padding=14),

            sessions_col,
        ], spacing=14, expand=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════════════════
    nav = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=88,
        bgcolor=SURFACE,
        indicator_color=ACCENT + "44",
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                label="Dashboard",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.TABLE_CHART_OUTLINED,
                selected_icon=ft.Icons.TABLE_CHART,
                label="Results",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                selected_icon=ft.Icons.PLAY_CIRCLE,
                label="Run",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.HISTORY,
                selected_icon=ft.Icons.HISTORY,
                label="History",
            ),
        ],
        leading=ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.BIOTECH, color=ACCENT, size=30),
                ft.Text("Spectra", size=11, color=ACCENT, weight=ft.FontWeight.BOLD),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3, tight=True),
            padding=ft.padding.only(top=18, bottom=10),
        ),
        on_change=lambda e: navigate(e.control.selected_index),
    )

    def navigate(index: int):
        current_view[0] = index
        nav.selected_index = index
        builders = [build_dashboard, build_results, build_runner, build_history]
        content_area.content = builders[index]()
        page.update()

    page.add(ft.Row([
        nav,
        ft.VerticalDivider(width=1, color=BORDER),
        content_area,
    ], expand=True, spacing=0))

    navigate(0)


if __name__ == "__main__":
    ft.app(target=main)
