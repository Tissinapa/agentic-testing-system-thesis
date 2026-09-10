"""
metrics/parse_agent_results.py
Parse all agent JSON result files into a clean Excel workbook.
Run from project root: python metrics/parse_agent_results.py
"""

import json
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


RESULTS_DIR = Path("results/agent")
OUTPUT_PATH = Path("results/agent_evaluations.xlsx")


# ── Style helpers ─────────────────────────────────────────────────────────────

def thin_border() -> Border:
    s = Side(style="thin")
    return Border(left=s, right=s, top=s, bottom=s)


def header_cell(ws, row: int, col: int, text: str):
    c = ws.cell(row=row, column=col, value=text)
    c.font      = Font(name="Calibri", bold=True, size=11)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border    = thin_border()


def data_cell(ws, row: int, col: int, value,
              center: bool = False, bold: bool = False):
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
        ws.column_dimensions[get_column_letter(i + 1)].width = w


# ── Classify evaluation type ──────────────────────────────────────────────────

def classify(ev: dict) -> str:
    test_id  = ev.get("test_id", "")
    endpoint = ev.get("endpoint", "")
    if test_id.startswith("WB-") or endpoint == "source_code":
        return "white-box"
    if test_id.startswith("TC-R"):
        return "reflection"
    return "standard"


# ── Build one sheet per result file ──────────────────────────────────────────

def build_sheet(wb, data: dict) -> int:
    meta        = data.get("meta", {})
    target      = meta.get("target", "unknown")
    mode        = meta.get("mode", "black")
    summary     = data.get("summary", {})
    evaluations = data.get("evaluations", [])

    if not evaluations:
        return 0

    # Unique sheet name
    base_name = f"{target}_{mode}"[:28]
    existing  = [s.title for s in wb.worksheets]
    name      = base_name
    counter   = 1
    while name in existing:
        name = f"{base_name}_{counter}"
        counter += 1

    ws = wb.create_sheet(name)
    ws.freeze_panes = "A3"

    # ── Metadata row ──
    meta_str = (
        f"Target: {target}  |  Mode: {mode}  |  "
        f"Tests executed: {summary.get('tests_executed', 0)}  |  "
        f"Bugs detected: {summary.get('bugs_detected', 0)}  |  "
        f"False positives: {summary.get('false_positives', 0)}  |  "
        f"Tokens: {meta.get('token_usage', 0):,}  |  "
        f"Timestamp: {meta.get('timestamp', '')[:19]}"
    )
    ws.merge_cells(f"A1:{get_column_letter(9)}1")
    m = ws.cell(row=1, column=1, value=meta_str)
    m.font      = Font(name="Calibri", size=10, italic=True)
    m.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 16

    # ── Headers ──
    headers = [
        "Test ID", "Type", "Endpoint",
        "Bug Detected", "Status Received", "Severity",
        "Verdict", "LLM Reasoning", "Recommendation"
    ]
    for i, h in enumerate(headers):
        header_cell(ws, 2, i + 1, h)
    ws.row_dimensions[2].height = 20

    # ── Data rows ──
    for i, ev in enumerate(evaluations):
        row  = i + 3
        bug  = ev.get("bug_detected", False)
        kind = classify(ev)

        data_cell(ws, row, 1, ev.get("test_id", ""),                           bold=True)
        data_cell(ws, row, 2, kind,                                             center=True)
        data_cell(ws, row, 3, ev.get("endpoint", ""))
        data_cell(ws, row, 4, "YES" if bug else "no",                          center=True, bold=bug)
        data_cell(ws, row, 5, ev.get("status_received", "") or "",             center=True)
        data_cell(ws, row, 6, (ev.get("severity") or "").upper() if ev.get("severity") else "", center=True)
        data_cell(ws, row, 7, ev.get("verdict", ""))
        data_cell(ws, row, 8, ev.get("reasoning") or ev.get("resoning", ""))
        data_cell(ws, row, 9, ev.get("recommendation") or "")
        ws.row_dimensions[row].height = 60

    set_widths(ws, [14, 10, 28, 12, 14, 10, 35, 50, 40])
    return len(evaluations)


# ── All evaluations combined sheet ────────────────────────────────────────────

def build_all_sheet(wb, all_rows: list[dict]):
    ws = wb.create_sheet("All Evaluations", 0)   # first sheet
    ws.freeze_panes = "A2"

    headers = [
        "Run", "App", "Mode", "Test ID", "Type",
        "Endpoint", "Bug Detected", "Severity",
        "Verdict", "LLM Reasoning", "Recommendation"
    ]
    for i, h in enumerate(headers):
        header_cell(ws, 1, i + 1, h)
    ws.row_dimensions[1].height = 20

    for i, r in enumerate(all_rows):
        row = i + 2
        bug = r["bug_detected"]
        data_cell(ws, row, 1,  r["run"],                                        bold=True)
        data_cell(ws, row, 2,  r["app"])
        data_cell(ws, row, 3,  r["mode"],                                       center=True)
        data_cell(ws, row, 4,  r["test_id"],                                    bold=True)
        data_cell(ws, row, 5,  r["kind"],                                       center=True)
        data_cell(ws, row, 6,  r["endpoint"])
        data_cell(ws, row, 7,  "YES" if bug else "no",                          center=True, bold=bug)
        data_cell(ws, row, 8,  (r["severity"] or "").upper() if r["severity"] else "", center=True)
        data_cell(ws, row, 9,  r["verdict"])
        data_cell(ws, row, 10, r["reasoning"])
        data_cell(ws, row, 11, r["recommendation"] or "")
        ws.row_dimensions[row].height = 60

    set_widths(ws, [18, 12, 10, 14, 10, 28, 12, 10, 35, 50, 40])


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not RESULTS_DIR.exists():
        print("No results/agent directory found.")
        return

    files = sorted(RESULTS_DIR.glob("*.json"))
    if not files:
        print("No agent JSON result files found.")
        return

    wb       = openpyxl.Workbook()
    wb.remove(wb.active)

    all_rows = []
    total    = 0

    for f in files:
        try:
            with open(f) as fp:
                data = json.load(fp)
        except Exception as e:
            print(f"Warning: could not load {f.name}: {e}")
            continue

        meta   = data.get("meta", {})
        target = meta.get("target", "unknown")
        mode   = meta.get("mode", "black")
        run    = f"{target} / {mode}"

        # Collect rows for All sheet
        for ev in data.get("evaluations", []):
            all_rows.append({
                "run":            run,
                "app":            target,
                "mode":           mode,
                "test_id":        ev.get("test_id", ""),
                "kind":           classify(ev),
                "endpoint":       ev.get("endpoint", ""),
                "bug_detected":   ev.get("bug_detected", False),
                "severity":       ev.get("severity"),
                "verdict":        ev.get("verdict", ""),
                "reasoning":      ev.get("reasoning") or ev.get("resoning", ""),
                "recommendation": ev.get("recommendation") or "",
            })

        count = build_sheet(wb, data)
        print(f"  {f.name}: {count} evaluations")
        total += count

    build_all_sheet(wb, all_rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT_PATH)
    print(f"\nSaved: {OUTPUT_PATH}")
    print(f"Total evaluation rows: {total}")


if __name__ == "__main__":
    main()