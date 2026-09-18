# hn-otel-stability-boundary-lab — Results

Cases: 10

| id | component_type | stability_level | compatibility_guarantee | semconv_stability | instrumentation_mode | backend_standardized |
|---|---|---|---|---|---|---|
| stable_api_compatibility | api | Stable | stable_major_bump_required | not_applicable | manual | False |
| development_no_guarantee | sdk | Development | no_stable_guarantee | not_applicable | manual | False |
| api_sdk_different_versions | api+sdk | Stable | stable_major_bump_required | not_applicable | manual | False |
| different_languages_different_versions | api | Stable | stable_major_bump_required | not_applicable | manual | False |
| stable_group_unstable_attribute | semantic_conventions | Mixed | mixed_no_uniform_guarantee | Development | manual | False |
| contrib_vs_core | contrib | Development | no_stable_guarantee | not_applicable | automatic | False |
| manual_instrumentation_valid | api | Stable | stable_major_bump_required | not_applicable | manual | False |
| automatic_instrumentation_mechanism | contrib | Stable | contrib_should_compatible | not_applicable | automatic | False |
| backend_behavior_separate | api | Stable | stable_major_bump_required | not_applicable | manual | False |
| mixed_semconv_stability | semantic_conventions | Mixed | mixed_no_uniform_guarantee | Mixed | not_applicable | False |

## Key invariants (per primary OTel sources)

- Stable API/SDK: backward-incompatible changes MUST NOT unless major version incremented (versioning-and-stability.md).
- Development: no stable guarantee; breaking changes MAY occur.
- API, SDK, Semantic Conventions, Contrib have independent version numbers (e.g., python api 1.24.0 vs sdk 1.31.0; python vs java differ).
- Contrib packages MAY have own version; SHOULD remain compatible, MAY break on downstream dependency (weaker than MUST).
- Stable convention group referencing Development OptIn attribute: attribute remains Development (group stability does not confer).
- Mixed stability: stable and development attributes coexist in same semconv version.
- Manual instrumentation remains valid; automatic instrumentation is one mechanism, not a requirement.
- Backend/UI behavior is separate implementation; client-spec compatibility does not standardize it.
- No overall 'OTel compliant' or 'production safe' verdict is emitted — read separate axes.

- **stable_api_compatibility**: component_type=api, stability=Stable, compat=stable_major_bump_required, semconv=not_applicable, instr=manual (required=False), backend_std=False
- **development_no_guarantee**: component_type=sdk, stability=Development, compat=no_stable_guarantee, semconv=not_applicable, instr=manual (required=False), backend_std=False
- **api_sdk_different_versions**: component_type=api+sdk, stability=Stable, compat=stable_major_bump_required, semconv=not_applicable, instr=manual (required=False), backend_std=False
- **different_languages_different_versions**: component_type=api, stability=Stable, compat=stable_major_bump_required, semconv=not_applicable, instr=manual (required=False), backend_std=False
- **stable_group_unstable_attribute**: component_type=semantic_conventions, stability=Mixed, compat=mixed_no_uniform_guarantee, semconv=Development, instr=manual (required=False), backend_std=False
- **contrib_vs_core**: component_type=contrib, stability=Development, compat=no_stable_guarantee, semconv=not_applicable, instr=automatic (required=False), backend_std=False
- **manual_instrumentation_valid**: component_type=api, stability=Stable, compat=stable_major_bump_required, semconv=not_applicable, instr=manual (required=False), backend_std=False
- **automatic_instrumentation_mechanism**: component_type=contrib, stability=Stable, compat=contrib_should_compatible, semconv=not_applicable, instr=automatic (required=False), backend_std=False
- **backend_behavior_separate**: component_type=api, stability=Stable, compat=stable_major_bump_required, semconv=not_applicable, instr=manual (required=False), backend_std=False
- **mixed_semconv_stability**: component_type=semantic_conventions, stability=Mixed, compat=mixed_no_uniform_guarantee, semconv=Mixed, instr=not_applicable (required=False), backend_std=False
