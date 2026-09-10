"""
metrics/export_excel.py
Export thesis comparison metrics to a clean Excel workbook.
Run from project root: python metrics/export_excel.py
"""

import json
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side

RESULTS_FILE  = Path("results/metrics_summary.json")
OUTPUT_FILE   = Path("results/thesis_metrics.xlsx")

USD_TO_EUR    = 0.8631
BLENDED_PER_M = 6.60


def usd(tokens: int) -> float:
    return (tokens / 1_000_000) * BLENDED_PER_M


def eur(tokens: int) -> float:
    return usd(tokens) * USD_TO_EUR


def thin_border() -> Border:
    s = Side(style="thin")
    return Border(left=s, right=s, top=s, bottom=s)


def header_cell(ws, row: int, col: int, text: str):
    c = ws.cell(row=row, column=col, value=text)
    c.font      = Font(name="Calibri", bold=True, size=11)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border    = thin_border()


def data_cell(ws, row: int, col: int, value, center: bool = False, bold: bool = False):
    c = ws.cell(row=row, column=col, value=value)
    c.font      = Font(name="Calibri", bold=bold, size=11)
    c.alignment = Alignment(
        horizontal="center" if center else "left",
        vertical="center",
        wrap_text=True
    )
    c.border = thin_border()


def set_widths(ws, widths: list[int]):
    for i, w in enumerate(widths):
        from openpyxl.utils import get_column_letter
        ws.column_dimensions[get_column_letter(i+1)].width = w


def load() -> list[dict]:
    with open(RESULTS_FILE) as f:
        return json.load(f)["results"]


def sheet_comparison(wb, results: list[dict]):
    ws = wb.create_sheet("Comparison Table")
    ws.freeze_panes = "A2"

    headers = [
        "Framework", "App", "Mode",
        "Tests Executed", "Tests Passed", "Bugs Detected",
        "False Positives", "Tokens Used"
    ]
    for i, h in enumerate(headers):
        header_cell(ws, 1, i+1, h)

    for i, r in enumerate(results):
        row = i + 2
        row_data = [
            r["framework"], r["app"], r["mode"],
            r.get("tests_executed", 0),
            r.get("tests_passed", 0),
            r["bugs_detected"],
            r["false_positives"],
            r["token_usage"] if r["token_usage"] > 0 else "N/A",
        ]
        for j, v in enumerate(row_data):
            data_cell(ws, row, j+1, v, center=isinstance(v, (int, float)))

    set_widths(ws, [20, 12, 10, 14, 14, 14, 14, 14])


def sheet_bugs(wb, results: list[dict]):
    ws = wb.create_sheet("Bug Detection")
    ws.freeze_panes = "A2"

    headers = ["App", "Framework", "Mode", "Bugs Detected", "False Positives", "FP Rate %"]
    for i, h in enumerate(headers):
        header_cell(ws, 1, i+1, h)

    row = 2
    for app in sorted(set(r["app"] for r in results)):
        for r in [x for x in results if x["app"] == app]:
            bugs  = r["bugs_detected"]
            fp    = r["false_positives"]
            total = bugs + fp
            fp_rate = round(fp / total * 100, 1) if total > 0 else 0
            for j, v in enumerate([r["app"], r["framework"], r["mode"],
                                    bugs, fp, f"{fp_rate}%"]):
                data_cell(ws, row, j+1, v, center=isinstance(v, (int, float)))
            row += 1

    set_widths(ws, [14, 20, 10, 14, 14, 12])


def sheet_efficiency(wb, results: list[dict]):
    ws = wb.create_sheet("Agent Efficiency")
    ws.freeze_panes = "A2"

    headers = [
        "App", "Mode", "Tests Executed", "Bugs Detected",
        "Tokens Used", "Cost USD", "Cost EUR",
        "Bugs / 1k Tokens", "EUR per Bug"
    ]
    for i, h in enumerate(headers):
        header_cell(ws, 1, i+1, h)

    agent = [r for r in results if r["framework"] == "AI Agent"]
    for i, r in enumerate(sorted(agent, key=lambda x: (x["app"], x["mode"]))):
        row    = i + 2
        tokens = r["token_usage"]
        bugs   = r["bugs_detected"]
        row_data = [
            r["app"], r["mode"],
            r.get("tests_executed", 0), bugs, tokens,
            f"${usd(tokens):.4f}", f"€{eur(tokens):.4f}",
            round(bugs / (tokens / 1000), 2) if tokens > 0 else 0,
            f"€{eur(tokens)/bugs:.4f}" if bugs > 0 else "N/A",
        ]
        for j, v in enumerate(row_data):
            data_cell(ws, row, j+1, v, center=isinstance(v, (int, float)))

    # Totals row
    total_row = len(agent) + 2
    total_t = sum(r["token_usage"] for r in agent)
    total_b = sum(r["bugs_detected"] for r in agent)
    totals = [
        "TOTAL", "all",
        sum(r.get("tests_executed", 0) for r in agent),
        total_b, total_t,
        f"${usd(total_t):.4f}", f"€{eur(total_t):.4f}",
        round(total_b / (total_t / 1000), 2) if total_t > 0 else 0,
        f"€{eur(total_t)/total_b:.4f}" if total_b > 0 else "N/A",
    ]
    for j, v in enumerate(totals):
        data_cell(ws, total_row, j+1, v,
                  center=isinstance(v, (int, float)), bold=True)

    # Pricing note
    note_row = total_row + 2
    ws.merge_cells(f"A{note_row}:I{note_row}")
    n = ws.cell(row=note_row, column=1,
                value=(f"Claude Sonnet 4-6: $3.00/M input + $15.00/M output | "
                       f"Blended: ${BLENDED_PER_M}/M | "
                       f"1 USD = {USD_TO_EUR} EUR (2 Sep 2026)"))
    n.font      = Font(name="Calibri", size=9, italic=True)
    n.alignment = Alignment(horizontal="left", vertical="center")

    set_widths(ws, [14, 10, 14, 14, 14, 12, 12, 16, 14])


def sheet_os(wb, results: list[dict]):
    ws = wb.create_sheet("OS Projects")
    ws.freeze_panes = "A2"

    headers = [
        "Project", "Framework", "Mode",
        "Tests Executed", "Bugs Detected", "False Positives", "Tokens"
    ]
    for i, h in enumerate(headers):
        header_cell(ws, 1, i+1, h)

    os_results = [r for r in results if "_os" in r["app"]]
    for i, r in enumerate(os_results):
        row = i + 2
        row_data = [
            r["app"], r["framework"], r["mode"],
            r.get("tests_executed", 0),
            r["bugs_detected"], r["false_positives"],
            r["token_usage"] if r["token_usage"] > 0 else "N/A",
        ]
        for j, v in enumerate(row_data):
            data_cell(ws, row, j+1, v, center=isinstance(v, (int, float)))

    note_row = len(os_results) + 3
    ws.merge_cells(f"A{note_row}:G{note_row}")
    n = ws.cell(row=note_row, column=1,
                value=("java_os = Swagger Petstore (petstore3.swagger.io) | "
                       "python_os = FastAPI Full Stack Template"))
    n.font      = Font(name="Calibri", size=9, italic=True)
    n.alignment = Alignment(horizontal="left", vertical="center")

    set_widths(ws, [16, 20, 10, 14, 14, 14, 14])


def main():
    results = load()
    print(f"Loaded {len(results)} result records")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    sheet_comparison(wb, results)
    sheet_bugs(wb, results)
    sheet_efficiency(wb, results)
    sheet_os(wb, results)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT_FILE)
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()