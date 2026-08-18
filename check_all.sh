#!/bin/bash
REPORT="diagnostic_report.txt"
echo "TaskFlow Diagnostic Report — $(date)" > "$REPORT"
echo "==========================================" >> "$REPORT"

section() {
    echo "" >> "$REPORT"
    echo "----- $1 -----" >> "$REPORT"
}

section "1. Templates referenced in app.py"
grep -n "render_template(" app.py >> "$REPORT" 2>&1

section "1b. Templates that actually exist in templates/"
ls templates/ >> "$REPORT" 2>&1

section "2. Static files referenced (app.py + templates)"
grep -rn "url_for('static'" app.py templates/*.html >> "$REPORT" 2>&1

section "2b. Static files that actually exist in static/"
ls static/ >> "$REPORT" 2>&1

section "3. Python syntax check (py_compile)"
find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" | while read -r f; do
    python3 -m py_compile "$f" 2>> "$REPORT" && echo "OK: $f" >> "$REPORT"
done

section "4. pyflakes (undefined names, bad imports)"
if ! command -v pyflakes >/dev/null 2>&1; then
    pip install pyflakes --quiet >> "$REPORT" 2>&1
fi
find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -exec pyflakes {} \; >> "$REPORT" 2>&1

section "5. pytest results"
if ! command -v pytest >/dev/null 2>&1; then
    pip install pytest --quiet >> "$REPORT" 2>&1
fi
pytest -v >> "$REPORT" 2>&1

echo "" >> "$REPORT"
echo "==========================================" >> "$REPORT"
echo "Diagnostic complete. See $REPORT for full details." >> "$REPORT"

echo ""
echo "=== SUMMARY ==="
echo "Full report saved to: $REPORT"
echo ""
echo "-- pytest result line: --"
tail -n 5 "$REPORT" | grep -E "passed|failed|error" || echo "(check $REPORT for details)"
echo ""
echo "Run: cat $REPORT   to see everything."
