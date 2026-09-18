# Verification — fresh unauthenticated HTTPS clone

Date (UTC): 2026-09-18T01:55:00Z
Repo: https://github.com/necat101/hn-otel-stability-boundary-lab
Tested revision (C): `a9fcd33d884b29df7c5c05c6f4454ace2db19c33`
Clone origin: `https://github.com/necat101/hn-otel-stability-boundary-lab.git` (public HTTPS, not file://)

## C — fresh-clone verification (unauthenticated HTTPS)

```
$ rm -rf /tmp/fresh-C && git clone https://github.com/necat101/hn-otel-stability-boundary-lab.git /tmp/fresh-C
Cloning into '/tmp/fresh-C'...

$ git -C /tmp/fresh-C rev-parse HEAD
a9fcd33d884b29df7c5c05c6f4454ace2db19c33

$ git -C /home/ubuntu/.openclaw/workspace/hn-otel-stability-boundary-lab rev-parse HEAD
a9fcd33d884b29df7c5c05c6f4454ace2db19c33
=> MATCH (fresh clone HEAD == local C == tested revision)

$ git -C /tmp/fresh-C remote get-url origin
https://github.com/necat101/hn-otel-stability-boundary-lab.git

$ python3 -m py_compile /tmp/fresh-C/evaluator.py && echo "py_compile evaluator.py: OK"
py_compile evaluator.py: OK

$ python3 -m py_compile /tmp/fresh-C/tests/test_stability_boundary.py && echo "py_compile tests: OK"
py_compile tests: OK

$ python3 /tmp/fresh-C/evaluator.py
Wrote /tmp/fresh-C/results.json and /tmp/fresh-C/RESULTS.md (10 cases)

$ bash /tmp/fresh-C/verify.sh
=== hn-otel-stability-boundary-lab verification ===
py_compile evaluator.py: OK
py_compile tests: OK
Running evaluator...
Wrote /tmp/fresh-C/results.json and /tmp/fresh-C/RESULTS.md (10 cases)
Running tests...
test_all_required_case_ids_present ... ok
test_api_sdk_different_versions_independent ... ok
test_automatic_instrumentation_not_required ... ok
test_backend_behavior_not_standardized ... ok
test_contrib_vs_core_independent ... ok
test_development_no_guarantee ... ok
test_different_languages_different_versions ... ok
test_evaluator_matches_oracle_core_fields ... ok
test_manual_instrumentation_valid ... ok
test_mixed_semconv_stability ... ok
test_no_overall_verdict_field ... ok
test_semantic_convention_warning_mixed ... ok
test_separate_outputs_present ... ok
test_stable_api_compatibility ... ok
test_stable_group_unstable_attribute_not_inherited ... ok
----------------------------------------------------------------------
Ran 15 tests in 0.011s
OK
Deterministic re-run check...
Wrote /tmp/fresh-C/results.json and /tmp/fresh-C/RESULTS.md (10 cases)
Diff generated outputs vs tracked...
Generated outputs match tracked (or not a git repo yet).
HEAD: a9fcd33d884b29df7c5c05c6f4454ace2db19c33
origin: https://github.com/necat101/hn-otel-stability-boundary-lab.git
status:
All local checks passed.

$ git -C /tmp/fresh-C diff --exit-code -- results.json RESULTS.md && echo "diff: no changes"
diff: no changes

$ git -C /tmp/fresh-C status --porcelain
(clean)
```

## What D does / does not do

D is documentation-only. D does not change `evaluator.py`, `fixtures/cases.json`, `tests/test_stability_boundary.py`, `results.json`, or `RESULTS.md`. D only records that C (`a9fcd33`) was fresh-clone matched and executed as above. D does not verify itself.

## GitHub Actions

`.github/workflows/ci.yml` runs `python3 evaluator.py`, `cat results.json`, `cat RESULTS.md`, `python3 -m unittest tests.test_stability_boundary -v`, and `bash verify.sh`. Workflow status for the closure revision is inspected via approved GitHub tooling and reported in the closure email / reply (actual returned state, not predicted).
