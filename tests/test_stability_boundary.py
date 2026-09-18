#!/usr/bin/env python3
"""
Independent oracle for hn-otel-stability-boundary-lab.

Re-derives expected classifications from raw fixture facts without calling
the evaluator's decision branches. Catches conflations across the boundary
stable API ≠ stable SDK ≠ stable semconv ≠ contrib ≠ instrumentation mode ≠ backend.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).parent.parent
FIXTURES = ROOT / "fixtures" / "cases.json"
RESULTS = ROOT / "results.json"


def load_cases():
    return {c["id"]: c for c in json.loads(FIXTURES.read_text())}


def load_results():
    return {r["id"]: r for r in json.loads(RESULTS.read_text())}


def oracle_compatibility(component_type, level):
    if level == "Stable" and component_type in ("api", "sdk", "api+sdk"):
        return "stable_major_bump_required"
    if level == "Stable" and component_type == "contrib":
        return "contrib_should_compatible"
    if level == "Mixed":
        return "mixed_no_uniform_guarantee"
    if level == "Development":
        return "no_stable_guarantee"
    return "unknown"


def oracle_semconv_stability(component_type, level, semconv):
    if component_type != "semantic_conventions":
        return "not_applicable"
    if semconv is None:
        return level
    if semconv.get("mixed") and "attributes" in semconv:
        stabs = {a["stability"] for a in semconv["attributes"]}
        if len(stabs) > 1:
            return "Mixed"
    if semconv.get("referenced_in_group") and semconv.get("group_stability") == "Stable" and semconv.get("attribute_stability") == "Development":
        return "Development"
    if semconv.get("attribute_stability"):
        return semconv["attribute_stability"]
    if semconv.get("group_stability"):
        return semconv["group_stability"]
    return level


class TestStabilityBoundary(unittest.TestCase):
    def test_all_required_case_ids_present(self):
        cases = load_cases()
        required = [
            "stable_api_compatibility",
            "development_no_guarantee",
            "api_sdk_different_versions",
            "different_languages_different_versions",
            "stable_group_unstable_attribute",
            "contrib_vs_core",
            "manual_instrumentation_valid",
            "automatic_instrumentation_mechanism",
            "backend_behavior_separate",
            "mixed_semconv_stability",
        ]
        for rid in required:
            self.assertIn(rid, cases, f"missing fixture {rid}")
        results = load_results()
        for rid in required:
            self.assertIn(rid, results, f"missing result {rid}")

    def test_no_overall_verdict_field(self):
        results = load_results()
        for rid, r in results.items():
            for banned in ("overall_compliant", "production_safe", "otel_compliant", "is_production_safe"):
                self.assertNotIn(banned, r, f"{rid} must not emit overall verdict '{banned}'")

    def test_stable_api_compatibility(self):
        cases = load_cases()
        results = load_results()
        r = results["stable_api_compatibility"]
        c = cases["stable_api_compatibility"]
        self.assertEqual(r["component_type"], c["component"]["component_type"])
        self.assertEqual(r["stability_level"], "Stable")
        self.assertEqual(r["compatibility_guarantee"], oracle_compatibility("api", "Stable"))
        self.assertTrue(r["stable_compatible"])
        self.assertEqual(r["semantic_convention_stability"], "not_applicable")
        self.assertEqual(r["backend_behavior_standardized"], False)

    def test_development_no_guarantee(self):
        results = load_results()
        r = results["development_no_guarantee"]
        self.assertEqual(r["stability_level"], "Development")
        self.assertEqual(r["compatibility_guarantee"], "no_stable_guarantee")
        self.assertFalse(r["stable_compatible"])
        # Development must NOT be treated as stable-compatible

    def test_api_sdk_different_versions_independent(self):
        cases = load_cases()
        results = load_results()
        c = cases["api_sdk_different_versions"]
        r = results["api_sdk_different_versions"]
        self.assertNotEqual(c["versioning"]["api_version"], c["versioning"]["sdk_version"])
        self.assertTrue(r["versioning_independent"])
        # API+SDK stable but versions differ — independent versioning rule
        self.assertEqual(r["compatibility_guarantee"], "stable_major_bump_required")
        # Must not conflate: stable API version does not force SDK to same number
        self.assertEqual(r["versioning"]["api_version"], "1.24.0")
        self.assertEqual(r["versioning"]["sdk_version"], "1.31.0")

    def test_different_languages_different_versions(self):
        cases = load_cases()
        results = load_results()
        c = cases["different_languages_different_versions"]
        lv = c["versioning"]["language_versions"]
        self.assertNotEqual(lv["python_api"], lv["java_api"])
        self.assertTrue(results["different_languages_different_versions"]["versioning_independent"])
        self.assertIn("Different language implementations", results["different_languages_different_versions"]["versioning_note"])

    def test_stable_group_unstable_attribute_not_inherited(self):
        cases = load_cases()
        results = load_results()
        c = cases["stable_group_unstable_attribute"]
        r = results["stable_group_unstable_attribute"]
        self.assertEqual(c["semantic_convention"]["group_stability"], "Stable")
        self.assertEqual(c["semantic_convention"]["attribute_stability"], "Development")
        # Oracle: attribute remains Development despite stable group
        self.assertEqual(r["semantic_convention_stability"], "Development")
        self.assertEqual(r["semconv_group_stability"], "Stable")
        self.assertEqual(r["semconv_attribute_stability"], "Development")
        self.assertFalse(r["semconv_attribute_inherits_stable"])
        self.assertFalse(r["stable_compatible"])  # Mixed has no uniform guarantee

    def test_mixed_semconv_stability(self):
        results = load_results()
        r = results["mixed_semconv_stability"]
        self.assertEqual(r["semantic_convention_stability"], "Mixed")
        self.assertEqual(r["compatibility_guarantee"], "mixed_no_uniform_guarantee")
        self.assertEqual(r["semconv_group_stability"], "Mixed")

    def test_contrib_vs_core_independent(self):
        cases = load_cases()
        results = load_results()
        c = cases["contrib_vs_core"]
        r = results["contrib_vs_core"]
        self.assertEqual(c["component"]["component_type"], "contrib")
        self.assertEqual(c["core_counterpart"]["component_type"], "api")
        self.assertEqual(c["core_counterpart"]["stability"], "Stable")
        # Contrib development: weaker guarantee than core stable
        self.assertEqual(r["compatibility_guarantee"], "no_stable_guarantee")
        self.assertFalse(r["stable_compatible"])
        self.assertTrue(r["versioning_independent"])
        # Must not treat contrib as having identical guarantees to core API
        core_compat = oracle_compatibility("api", "Stable")
        self.assertNotEqual(r["compatibility_guarantee"], core_compat)

    def test_manual_instrumentation_valid(self):
        results = load_results()
        r = results["manual_instrumentation_valid"]
        self.assertEqual(r["instrumentation_mode"], "manual")
        self.assertFalse(r["instrumentation_is_required"])
        self.assertIn("Manual instrumentation remains valid", r["instrumentation_note"])

    def test_automatic_instrumentation_not_required(self):
        results = load_results()
        r = results["automatic_instrumentation_mechanism"]
        self.assertEqual(r["instrumentation_mode"], "automatic")
        self.assertFalse(r["instrumentation_is_required"])
        self.assertIn("not a requirement", r["instrumentation_note"])
        # Automatic is one mechanism, not mandatory for using OTel

    def test_backend_behavior_not_standardized(self):
        results = load_results()
        r = results["backend_behavior_separate"]
        self.assertEqual(r["backend_behavior"], "trace_ui_sampling_display")
        self.assertFalse(r["backend_behavior_standardized"])
        self.assertTrue("separate implementation" in r["backend_note"] or "does not standardize" in r["backend_note"])
        # Client-spec compatibility does NOT standardize backend rendering
        # Also check stable API case: even with stable API, backend remains false
        r2 = results["stable_api_compatibility"]
        self.assertFalse(r2["backend_behavior_standardized"])

    def test_evaluator_matches_oracle_core_fields(self):
        cases = load_cases()
        results = load_results()
        for rid, c in cases.items():
            r = results[rid]
            exp_compat = oracle_compatibility(c["component"]["component_type"], c["stability"]["level"])
            self.assertEqual(r["compatibility_guarantee"], exp_compat, f"{rid} compatibility mismatch")
            exp_sem = oracle_semconv_stability(c["component"]["component_type"], c["stability"]["level"], c.get("semantic_convention"))
            self.assertEqual(r["semantic_convention_stability"], exp_sem, f"{rid} semconv mismatch")
            # instrumentation oracle
            mode = c.get("instrumentation", {}).get("mode")
            exp_mode = mode if mode in ("manual", "automatic") else "not_applicable"
            self.assertEqual(r["instrumentation_mode"], exp_mode, f"{rid} instrumentation mismatch")
            # backend oracle is always false per spec
            self.assertFalse(r["backend_behavior_standardized"], f"{rid} backend must be false")

    def test_separate_outputs_present(self):
        results = load_results()
        required_fields = ["component_type", "stability_level", "compatibility_guarantee", "semantic_convention_stability", "instrumentation_mode", "backend_behavior_standardized"]
        for rid, r in results.items():
            for f in required_fields:
                self.assertIn(f, r, f"{rid} missing required output field {f}")

    def test_semantic_convention_warning_mixed(self):
        # Per versioning spec: API MUST become stable before SDK; signals MAY become stable component-by-component
        # None of the stable API guarantees should be extended to development contrib or mixed semconv
        results = load_results()
        self.assertEqual(results["stable_group_unstable_attribute"]["stability_level"], "Mixed")
        self.assertEqual(results["mixed_semconv_stability"]["stability_level"], "Mixed")
        # Both mixed cases must not claim stable_compatible true
        self.assertFalse(results["stable_group_unstable_attribute"]["stable_compatible"])
        self.assertFalse(results["mixed_semconv_stability"]["stable_compatible"])


if __name__ == "__main__":
    unittest.main()
