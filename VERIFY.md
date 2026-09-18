# Verification — fresh unauthenticated HTTPS clone

Date (UTC): 2026-09-18T01:37:00Z
Repo: https://github.com/necat101/hn-otel-stability-boundary-lab
Tested revision (A): `f6f0035bfd4e911e26b9715590f0087404141f0f`
Clone origin: `https://github.com/necat101/hn-otel-stability-boundary-lab.git` (public HTTPS, not file://)

## A — fresh-clone verification (unauthenticated HTTPS)

```
$ rm -rf /tmp/fresh-otel-A && git clone https://github.com/necat101/hn-otel-stability-boundary-lab.git /tmp/fresh-otel-A
Cloning into '/tmp/fresh-otel-A'...

$ git -C /tmp/fresh-otel-A rev-parse HEAD
f6f0035bfd4e911e26b9715590f0087404141f0f

$ git -C /home/ubuntu/.openclaw/workspace/hn-otel-stability-boundary-lab rev-parse HEAD
f6f0035bfd4e911e26b9715590f0087404141f0f
=> MATCH (fresh clone HEAD == local A == tested revision)

$ git -C /tmp/fresh-otel-A remote get-url origin
https://github.com/necat101/hn-otel-stability-boundary-lab.git

$ python3 -m py_compile /tmp/fresh-otel-A/evaluator.py && echo "py_compile evaluator.py: OK"
py_compile evaluator.py: OK

$ python3 -m py_compile /tmp/fresh-otel-A/tests/test_stability_boundary.py && echo "py_compile tests: OK"
py_compile tests: OK

$ python3 /tmp/fresh-otel-A/evaluator.py
Wrote /tmp/fresh-otel-A/results.json and /tmp/fresh-otel-A/RESULTS.md (10 cases)

$ python3 -m unittest tests.test_stability_boundary -v  # fresh clone (cd /tmp/fresh-otel-A)
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

$ bash /tmp/fresh-otel-A/verify.sh
=== hn-otel-stability-boundary-lab verification ===
py_compile evaluator.py: OK
py_compile tests: OK
Running evaluator...
Wrote /tmp/fresh-otel-A/results.json and /tmp/fresh-otel-A/RESULTS.md (10 cases)
Running tests...
[... 15 tests OK ...]
Deterministic re-run check...
Wrote /tmp/fresh-otel-A/results.json and /tmp/fresh-otel-A/RESULTS.md (10 cases)
Diff generated outputs vs tracked...
Generated outputs match tracked (or not a git repo yet).
HEAD: f6f0035bfd4e911e26b9715590f0087404141f0f
origin: https://github.com/necat101/hn-otel-stability-boundary-lab.git
status:
All local checks passed.

$ git -C /tmp/fresh-otel-A diff --exit-code -- results.json RESULTS.md && echo "diff: no changes"
diff: no changes

$ git -C /tmp/fresh-otel-A status --porcelain
(clean)
```

## What B does / does not do

B is documentation-only. B does not change `evaluator.py`, `fixtures/cases.json`, `tests/test_stability_boundary.py`, `results.json`, or `RESULTS.md`. B only records that A (`f6f0035`) was fresh-clone matched and executed as above. B does not verify itself.

## GitHub Actions

`.github/workflows/ci.yml` runs `python3 evaluator.py`, `cat results.json`, `cat RESULTS.md`, `python3 -m unittest tests.test_stability_boundary -v`, and `bash verify.sh`. Workflow status is inspected via approved GitHub tooling and reported in the closure email / grading reply.
