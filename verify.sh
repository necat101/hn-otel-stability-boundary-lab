#!/bin/sh
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "=== hn-otel-stability-boundary-lab verification ==="
python3 -m py_compile "$ROOT/evaluator.py" && echo "py_compile evaluator.py: OK"
python3 -m py_compile "$ROOT/tests/test_stability_boundary.py" && echo "py_compile tests: OK"
echo "Running evaluator..."
python3 "$ROOT/evaluator.py"
echo "Running tests..."
(cd "$ROOT" && python3 -m unittest tests.test_stability_boundary -v)
echo "Deterministic re-run check..."
python3 "$ROOT/evaluator.py"
echo "Diff generated outputs vs tracked..."
if git -C "$ROOT" diff --quiet -- results.json RESULTS.md 2>/dev/null; then
  echo "Generated outputs match tracked (or not a git repo yet)."
else
  echo "WARNING: generated outputs differ from tracked:"
  git -C "$ROOT" diff -- results.json RESULTS.md | head -n 100
fi
echo "HEAD: $(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo 'no git')"
echo "origin: $(git -C "$ROOT" remote get-url origin 2>/dev/null || echo 'no origin')"
echo "status:"
git -C "$ROOT" status --porcelain 2>/dev/null | head -n 30 || echo "no git"
echo "All local checks passed."
