"""
tools/verify_pages.py
=====================
Headless smoke check for the Streamlit application.

It uses ``streamlit.testing.v1.AppTest`` to execute ``app.py`` once per page and
reports whether the page rendered without an exception.  This is the quick
"did I break the app?" check used while building each module - it is *not* a full
automated test suite (the brief only asks for manual page verification, this just
makes that verification repeatable).

Usage
-----
    python tools/verify_pages.py
    python tools/verify_pages.py --out data/evaluation/ui_smoke_report.txt
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PAGES: List[str] = [
    "🏠 Dashboard",
    "🩺 Crop Doctor",
    "🌦️ Weather & Risk",
    "🧮 Fertilizer Calculator",
    "🔐 Product Verifier",
    "🏛️ Government Schemes",
    "🚜 Equipment Rental",
    "🤖 AI Agriculture Assistant",
]

def check_page(page: str, timeout: int) -> List[str]:
    """Run the app with ``page`` selected; return the list of problems found."""
    from streamlit.testing.v1 import AppTest

    problems: List[str] = []
    app = AppTest.from_file("app.py", default_timeout=timeout)
    try:
        app.run()
        app.session_state["page"] = page
        app.run()
    except Exception:
        problems.append("AppTest crashed:\n" + traceback.format_exc())
        return problems

    for exception in app.exception:
        problems.append(f"exception: {exception.value}")
    for error in app.error:
        problems.append(f"st.error: {error.value}")

    # Pages render their heading either with st.title() or with the styled hero block.
    headings = [title.value for title in app.title]
    headings += [
        block.value for block in app.markdown if '<div class="agv-hero"' in str(block.value)
    ]
    if not headings:
        problems.append("no page heading was rendered")
    else:
        problems.append(f"rendered heading: {headings[0][:80]}")
    return problems

def main() -> int:
    parser = argparse.ArgumentParser(description="Headless Streamlit page smoke check.")
    parser.add_argument("--out", default=None, help="also write the report to this file")
    parser.add_argument("--timeout", type=int, default=300, help="seconds per page run")
    args = parser.parse_args()

    # The page names contain emoji; make sure the console can always print them.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pragma: no cover - very old/odd consoles
        pass

    lines: List[str] = ["AgriVision - Streamlit page smoke check", "=" * 60]
    failures = 0
    for page in PAGES:
        problems = check_page(page, args.timeout)
        hard_failures = [
            problem for problem in problems
            if problem.startswith(("exception:", "st.error:", "AppTest crashed", "no st.title"))
        ]
        status = "FAIL" if hard_failures else "PASS"
        if hard_failures:
            failures += 1
        lines.append(f"[{status}] {page}")
        for problem in problems:
            lines.append(f"        {problem}")

    lines.append("=" * 60)
    lines.append(f"pages checked: {len(PAGES)} | failures: {failures}")
    report = "\n".join(lines)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report + "\n", encoding="utf-8")
    try:
        print(report)
    except UnicodeEncodeError:  # pragma: no cover - console encoding guard
        print(report.encode("ascii", "replace").decode("ascii"))
    if args.out:
        print(f"\n[ok] report written to {args.out}")
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
