#!/usr/bin/env python3
"""
Deterministic classifier for hn-otel-stability-boundary-lab.

Boundary: stable API ≠ stable SDK ≠ stable semantic convention ≠ contrib stability
          ≠ instrumentation mode ≠ backend behavior

No collectors, telemetry backends, containers, network traces, SDK installation,
benchmarks, or fabricated performance results — stdlib only + synthetic records.

Reads fixtures/cases.json and writes results.json + RESULTS.md
Exit 0.

Intentionally does NOT emit an overall "OTel compliant" or "production safe" verdict.
Consumers must read the separate axes:
  component_type, stability_level, compatibility_guarantee,
  semantic_convention_stability, instrumentation_mode, backend_behavior_standardized
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).parent
FIXTURES = ROOT / "fixtures" / "cases.json"
RESULTS_JSON = ROOT / "results.json"
RESULTS_MD = ROOT / "RESULTS.md"


def classify_compatibility(component_type: str, stability_level: str) -> dict:
    ct = component_type or ""
    lvl = stability_level or ""
    if lvl == "Stable" and ct in ("api", "sdk", "api+sdk"):
        return {"compatibility_guarantee": "stable_major_bump_required", "stable_compatible": True,
                "note": "Stable API/SDK: backward-incompatible changes MUST NOT be made unless major version incremented; existing calls MUST continue to compile/function across minor versions."}
    if lvl == "Stable" and ct == "contrib":
        return {"compatibility_guarantee": "contrib_should_compatible", "stable_compatible": False,
                "note": "Contrib Stable SHOULD remain backward compatible; MAY break if downstream dependency breaks — weaker than API/SDK MUST."}
    if lvl == "Mixed":
        return {"compatibility_guarantee": "mixed_no_uniform_guarantee", "stable_compatible": False,
                "note": "Mixed stability: stable groups and development attributes coexist; no uniform guarantee across all fields."}
    if lvl == "Development":
        return {"compatibility_guarantee": "no_stable_guarantee", "stable_compatible": False,
                "note": "Development: breaking changes and performance issues MAY occur; long-term dependencies SHOULD NOT be taken."}
    return {"compatibility_guarantee": "unknown", "stable_compatible": False, "note": "Unknown stability level."}


def classify_semconv(component_type: str, stability_level: str, semconv) -> dict:
    if component_type != "semantic_conventions":
        return {"semantic_convention_stability": "not_applicable", "group_stability": None, "attribute_stability": None, "attribute_inherits_stable": None,
                "note": "Not a semantic-conventions component."}
    if semconv is None:
        lvl = stability_level
        return {"semantic_convention_stability": lvl, "group_stability": lvl, "attribute_stability": None, "attribute_inherits_stable": None,
                "note": "No per-attribute detail; signal-level stability reported."}
    if semconv.get("mixed") and "attributes" in semconv:
        stabilities = {a["stability"] for a in semconv["attributes"]}
        if len(stabilities) > 1:
            return {"semantic_convention_stability": "Mixed", "group_stability": semconv.get("group_stability"), "attribute_stability": None, "attribute_inherits_stable": False,
                    "note": "Semantic conventions can contain mixed stability; Stable and Development attributes coexist in same version."}
    if semconv.get("referenced_in_group") and semconv.get("group_stability") == "Stable" and semconv.get("attribute_stability") == "Development":
        return {"semantic_convention_stability": "Development", "group_stability": "Stable", "attribute_stability": "Development",
                "attribute_inherits_stable": False,
                "note": "Stable convention group referencing Development OptIn attribute: attribute remains Development; group stability does NOT make attribute stable."}
    gs = semconv.get("group_stability")
    attr_s = semconv.get("attribute_stability")
    if attr_s:
        return {"semantic_convention_stability": attr_s, "group_stability": gs, "attribute_stability": attr_s,
                "attribute_inherits_stable": False if gs == "Stable" and attr_s == "Development" else None,
                "note": "Per-attribute stability reported; group stability does not automatically confer to unstable attributes."}
    if gs:
        return {"semantic_convention_stability": gs, "group_stability": gs, "attribute_stability": None, "attribute_inherits_stable": None,
                "note": "Group stability reported."}
    return {"semantic_convention_stability": stability_level, "group_stability": None, "attribute_stability": None, "attribute_inherits_stable": None, "note": "Fallback to signal level."}


def classify(rec: dict) -> dict:
    rid = rec["id"]
    comp = rec.get("component") or {}
    stability = rec.get("stability") or {}
    versioning = rec.get("versioning") or {}
    semconv = rec.get("semantic_convention")
    instr = rec.get("instrumentation") or {}
    backend = rec.get("backend") or {}

    component_type = comp.get("component_type")
    stability_level = stability.get("level")
    compat = classify_compatibility(component_type, stability_level)
    sem = classify_semconv(component_type, stability_level, semconv)
    mode = instr.get("mode")
    if mode in ("manual", "automatic"):
        instrumentation_mode = mode
    elif mode is None:
        instrumentation_mode = "not_applicable"
    else:
        instrumentation_mode = str(mode)
    instrumentation_is_required = bool(instr.get("is_required", False))
    instrumentation_note = "Manual instrumentation remains valid; automatic is one mechanism, not a requirement." if instrumentation_mode in ("manual", "automatic") else "No instrumentation mode applicable."
    backend_behavior_standardized = bool(backend.get("standardized_by_client_spec", False))
    api_v = versioning.get("api_version")
    sdk_v = versioning.get("sdk_version")
    lang_vs = versioning.get("language_versions")
    contrib_v = versioning.get("contrib_version")
    versioning_independent = None
    versioning_note = None
    if api_v and sdk_v and api_v != sdk_v:
        versioning_independent = True
        versioning_note = "API, SDK, Semantic Conventions, and Contrib have independent version numbers (e.g., api 1.24.0 vs sdk 1.31.0) per versioning spec."
    elif lang_vs and len(set(lang_vs.values())) > 1:
        versioning_independent = True
        versioning_note = "Different language implementations have independent version numbers (e.g., python api 1.24.0 vs java api 1.32.1)."
    elif component_type == "contrib" and contrib_v:
        versioning_independent = True
        versioning_note = "Contrib packages MAY have own version number independent of API/SDK/SemConv."
    else:
        versioning_independent = False
        versioning_note = "No version independence asserted in this case."
    result = {
        "id": rid,
        "component_type": component_type,
        "stability_level": stability_level,
        "compatibility_guarantee": compat["compatibility_guarantee"],
        "stable_compatible": compat["stable_compatible"],
        "compatibility_note": compat["note"],
        "semantic_convention_stability": sem["semantic_convention_stability"],
        "semconv_group_stability": sem["group_stability"],
        "semconv_attribute_stability": sem["attribute_stability"],
        "semconv_attribute_inherits_stable": sem["attribute_inherits_stable"],
        "semconv_note": sem["note"],
        "instrumentation_mode": instrumentation_mode,
        "instrumentation_is_required": instrumentation_is_required,
        "instrumentation_note": instrumentation_note,
        "backend_behavior_standardized": backend_behavior_standardized,
        "backend_behavior": backend.get("behavior"),
        "backend_note": backend.get("note") or ("Backend/UI rendering is separate implementation behavior; client-spec compatibility does not standardize it." if backend.get("behavior") else "No backend behavior in this case."),
        "versioning_independent": versioning_independent,
        "versioning_note": versioning_note,
        "versioning": versioning,
    }
    return result


def main():
    cases = json.loads(FIXTURES.read_text())
    results = [classify(c) for c in cases]
    RESULTS_JSON.write_text(json.dumps(results, indent=2) + "\n")
    lines = []
    lines.append("# hn-otel-stability-boundary-lab — Results")
    lines.append("")
    lines.append(f"Cases: {len(results)}")
    lines.append("")
    lines.append("| id | component_type | stability_level | compatibility_guarantee | semconv_stability | instrumentation_mode | backend_standardized |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in results:
        lines.append(f"| {r['id']} | {r['component_type']} | {r['stability_level']} | {r['compatibility_guarantee']} | {r['semantic_convention_stability']} | {r['instrumentation_mode']} | {r['backend_behavior_standardized']} |")
    lines.append("")
    lines.append("## Key invariants (per primary OTel sources)")
    lines.append("")
    lines.append("- Stable API/SDK: backward-incompatible changes MUST NOT unless major version incremented (versioning-and-stability.md).")
    lines.append("- Development: no stable guarantee; breaking changes MAY occur.")
    lines.append("- API, SDK, Semantic Conventions, Contrib have independent version numbers (e.g., python api 1.24.0 vs sdk 1.31.0; python vs java differ).")
    lines.append("- Contrib packages MAY have own version; SHOULD remain compatible, MAY break on downstream dependency (weaker than MUST).")
    lines.append("- Stable convention group referencing Development OptIn attribute: attribute remains Development (group stability does not confer).")
    lines.append("- Mixed stability: stable and development attributes coexist in same semconv version.")
    lines.append("- Manual instrumentation remains valid; automatic instrumentation is one mechanism, not a requirement.")
    lines.append("- Backend/UI behavior is separate implementation; client-spec compatibility does not standardize it.")
    lines.append("- No overall 'OTel compliant' or 'production safe' verdict is emitted — read separate axes.")
    lines.append("")
    for r in results:
        lines.append(f"- **{r['id']}**: component_type={r['component_type']}, stability={r['stability_level']}, compat={r['compatibility_guarantee']}, semconv={r['semantic_convention_stability']}, instr={r['instrumentation_mode']} (required={r['instrumentation_is_required']}), backend_std={r['backend_behavior_standardized']}")
    lines.append("")
    # normalize: exactly one trailing newline
    RESULTS_MD.write_text("\n".join(lines).rstrip("\n") + "\n")
    print(f"Wrote {RESULTS_JSON} and {RESULTS_MD} ({len(results)} cases)")


if __name__ == "__main__":
    main()
