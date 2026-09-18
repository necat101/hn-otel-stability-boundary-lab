# hn-otel-stability-boundary-lab

Audit for **HN 49391553 — “OTel isn’t going well”**

Tests the platform-team claim:

> “Because OpenTelemetry is stable, its API, SDK, semantic conventions, contrib instrumentation, automatic instrumentation, and backend behavior all share the same compatibility guarantees across languages.”

**Verdict: that claim collapses six distinct boundaries.** OTel's versioning spec permits component-by-component stability, independent version numbers per component and per language, mixed stability inside semantic conventions, weaker contrib guarantees than core API/SDK, automatic instrumentation as one mechanism among others, and backend rendering as separate implementation behavior.

## Boundary under test

| Layer | Meaning | Primary source |
|---|---|---|
| **API stability** | `Stable` API: backward-incompatible changes MUST NOT unless major bumps; calls MUST compile/function across minor versions | `versioning-and-stability.md` § API Stability |
| **SDK stability** | `Stable` SDK: public plugin interfaces + constructors MUST remain backward compatible | same doc § SDK Stability |
| **Development (no guarantee)** | `Development`: breaking changes MAY occur; long-term deps SHOULD NOT be taken | same doc § Development |
| **Version numbers** | API, SDK, Semantic Conventions, and Contrib have **independent** version numbers; languages also independent | same doc § Version numbers |
| **Contrib stability** | Contrib SHOULD remain compatible; MAY break on downstream dep; weaker than API/SDK MUST | same doc § Contrib Stability |
| **Semantic Conventions — mixed** | Stable group referencing Development OptIn attribute → attribute remains Development | `semconv/resource`, schema/docs, versioning spec § Semantic Conventions Stability |
| **Instrumentation mode** | Automatic vs manual are mechanisms; automatic is not a requirement to use OTel | OTel docs: manual vs auto instrumentation |
| **Backend behavior** | Backend/UI rendering is **not** standardized by client-spec compatibility | versioning-and-stability scope note (“OpenTelemetry clients” ≠ spec nor Collector) |

Rule: **stable API ≠ stable SDK ≠ stable semconv ≠ contrib stability ≠ instrumentation mode ≠ backend behavior**

## What the OTel sources actually say (verified 2026-09-18)

- **Four components with independent versioning:** `API`, `SDK`, `Semantic Conventions`, and `Contrib` are single packages each (Contrib may be multiple), versioned via SemVer 2.0 with clarifications. Example: `opentelemetry-python-api` at `v1.2.3` while `opentelemetry-python-sdk` at `v2.3.1` is explicitly allowed. Different language implementations also have independent numbers (e.g., Python `1.2.8` vs Java `1.3.2`) and are independent of the spec version they implement. ([versioning-and-stability.md § Version numbers](https://opentelemetry.io/docs/specs/otel/versioning-and-stability/), [OTEPS 0143](https://github.com/open-telemetry/oteps/blob/main/text/0143-versioning-and-stability.md))

- **Stability per signal component:** Development → Stable (→ Deprecated → Removed). A signal MAY become stable component-by-component in order API → Semantic Conventions → API Contrib → SDK → SDK Contrib. API MUST become stable before other components. Once Stable, rules apply until end of existence. ([same doc § Signal lifecycle / Stable](https://opentelemetry.io/docs/specs/otel/versioning-and-stability/))

- **Semantic conventions separately and mixed:** SemConv has its own version and schema; semconv documents may be `Mixed` status. A Stable group (e.g., `telemetry.sdk` Stable, `http` stable group) does not make a referenced Development OptIn attribute stable. GenAI `gen_ai.*` conventions as of `v1.42.0` moved to a dedicated repo and remain Development (renames expected). ([betterstack semconv guide](https://betterstack.com/community/guides/observability/opentelemetry-semantic-conventions/), [uptrace semconv](https://uptrace.dev/opentelemetry/semconv), [resource semconv](https://opentelemetry.io/docs/specs/semconv/resource/))

- **Contrib ≠ Core:** Contrib packages SHOULD stay compatible with latest API/SDK/SemConv; public portions SHOULD remain backward compatible, but MAY break when required downstream dependency breaks — with recommendation to ship new package rather than break existing. Weaker guarantee than API/SDK MUST. Same source § Contrib Stability.

- **Instrumentation modes:** Manual vs automatic are instrumentation mechanisms; automatic instrumentation is one mechanism, not a requirement for using OTel. Performance and abstraction trade-offs discussed in thread do not change normative spec guarantees.

- **Backend/UI is separate:** `versioning-and-stability.md` states “OpenTelemetry” and “language implementations” in that doc mean **clients** — not the spec or the Collector. Client-spec compatibility does not dictate or standardize backend/UI rendering or sampling display.

## HN 49391553 audit (comments actually retrieved — via HN Firebase + Algolia)

Quoted text is abbreviated; IDs and authors are exact so you can re-fetch `https://hacker-news.firebaseio.com/v0/item/<id>.json`.

| # | Proposition seen on thread | Source | Assessment |
|---|---|---|---|
| 1 | “The SDKs have terrible performance overhead for instrumentation and are … highly resistant to integrating the output of better performing (or just preexisting) instrumentation. In Python and Ruby … CPU cost of all the mandatory abstraction is way too high.” | **kalkin · 49400018** | **SDKs are the problem, not necessarily the spec.** Consistent with boundary `Stable API ≠ Stable SDK` and independent versioning — SDK behavior/complexity is separable from spec stability. Fixture `development_no_guarantee` / `stable_api_compatibility` tests this separation. |
| 2 | “What I find confusing about this is that otel is two things. 1. A spec 2. A ref implementation … if there's complaints about (2), that should trigger an ecosystem of alternative implementations that are guaranteed to be compatible because of (1).” | **growse · 49431601** | **OTel is both spec and implementation ecosystem.** Matches docs: “OpenTelemetry clients … do NOT refer to the specification or the Collector” vs OTEPS 0143 that clients follow spec versioning. Compatibility is not uniform via one global version. |
| 3 | “I like the end result of … tracing …, but the SDKs have been a nightmare. Too much emphasis on automatic instrumentation, Java-isms, everything is stateful and abstracted away.” | **osener · 49397084** | **Automatic instrumentation adds unwanted complexity (per comment).** Automatic is one instrumentation mechanism, not a requirement; manual remains valid (fixtures `manual_instrumentation_valid`, `automatic_instrumentation_mechanism`). |
| 4 | “What always puzzles me … is that tracing, metrics and logs are all designed independently. I wish … just annotate my code base once, and let the ultimate decision … be dynamic at runtime.” + reply “How would you represent metrics as traces? You cannot … metrics are something else …” | **EdSchouten · 49396130** (prompt) + **fuzzy2 · 49397362** (rebuttal) | **Traces, metrics, logs have intentionally distinct data models.** Distinct signals MAY stabilize independently; API MUST go stable first. Thread debate does not collapse them into one data model. |

If a comment you need is missing, fetch it directly — these are not invented. `python3 -c "import urllib.request,json;print(json.load(urllib.request.urlopen('https://hacker-news.firebaseio.com/v0/item/49400018.json')))"`

## Lab design

Pure **Python stdlib + shell**, no collectors, no telemetry backends, no containers, no network traces, no SDK installation, no benchmarks, no fabricated performance results. Every situation is a synthetic JSON record; the evaluator answers a *classification question* (“what stability/compatibility does this evidence actually establish?”), not “is OTel production safe?”

### Fixtures (`fixtures/cases.json`)

10 synthetic cases — each carries facts the classifier must interpret:

| id | Tests |
|---|---|
| `stable_api_compatibility` | Stable API — `stable_major_bump_required`, `stable_compatible=true` |
| `development_no_guarantee` | Development SDK signal — `no_stable_guarantee`, no stable promise |
| `api_sdk_different_versions` | API 1.24.0 vs SDK 1.31.0 — independent version numbers |
| `different_languages_different_versions` | Python api 1.24.0 vs Java api 1.32.1 — languages independent |
| `stable_group_unstable_attribute` | Stable http group referencing Development OptIn `http.request.resend_count` — attribute stays Development, `attribute_inherits_stable=false` |
| `contrib_vs_core` | Contrib `0.50b1` Development vs Core api `1.24.0` Stable — weaker guarantee, independent versioning |
| `manual_instrumentation_valid` | Manual mode — valid, `instrumentation_is_required=false` |
| `automatic_instrumentation_mechanism` | Automatic mode — one mechanism, `instrumentation_is_required=false` |
| `backend_behavior_separate` | Backend trace UI sampling display — `backend_behavior_standardized=false` despite client-spec stable |
| `mixed_semconv_stability` | Resource/http semconv Mixed (`service.name` Stable + `k8s.pod.uid` Development) — `Mixed`, `mixed_no_uniform_guarantee` |

### Evaluator (`evaluator.py`)

`python3 evaluator.py` reads `fixtures/cases.json`, derives six output axes per case:

```
component_type               api | sdk | api+sdk | semantic_conventions | contrib
stability_level              Stable | Development | Mixed
compatibility_guarantee      stable_major_bump_required | no_stable_guarantee | mixed_no_uniform_guarantee | contrib_should_compatible
semantic_convention_stability Stable | Development | Mixed | not_applicable
instrumentation_mode         manual | automatic | not_applicable
backend_behavior_standardized bool (always false per spec)
+ instrumentation_is_required (always false), versioning_independent, semconv_attribute_inherits_stable
```

No `overall_compliant` / `production_safe` / `otel_compliant` field is emitted. Exit 0; writes `results.json` + `RESULTS.md`.

### Tests (`tests/test_stability_boundary.py`)

Independent oracle — re-derives expected classifications from raw component/stability facts without calling the evaluator's decision branches. Catches:

- treating Development as having stable guarantee
- conflating API/SDK/SemConv/Contrib into one global “everything stable” guarantee
- assuming API and SDK share same version number in same language
- assuming all languages share same version number
- assuming stable convention group makes referenced unstable attribute stable
- assuming mixed stability has uniform stable guarantee
- treating contrib as having identical MUST guarantees as core API
- treating automatic instrumentation as required for using OTel
- treating backend/UI rendering as standardized by client-spec compatibility
- importing an overall compliant/production-safe verdict

```
python3 -m unittest tests/test_stability_boundary.py -v
```

### Verification

```sh
./verify.sh            # local deterministic evaluator/test check
cat RESULTS.md         # recorded actual output
cat VERIFY.md          # public HTTPS fresh-clone transcript (see VERIFY.md procedure)
```

## Quick start

```sh
git clone https://github.com/necat101/hn-otel-stability-boundary-lab.git
cd hn-otel-stability-boundary-lab
python3 evaluator.py
python3 -m unittest tests/test_stability_boundary.py -v
./verify.sh
```

## Sources inspected 2026-09-18

- HN item `49391553` + comments via `hacker-news.firebaseio.com` and `hn.algolia.com/api/v1/items/49391553` (IDs above)
- `https://opentelemetry.io/docs/specs/otel/versioning-and-stability/` (fetched 2026-09-18; Stable status; defines API/SDK/Contrib/SemConv stability + Version numbers)
- `https://github.com/open-telemetry/oteps/blob/main/text/0143-versioning-and-stability.md` (OTEPS 0143, same content family)
- `https://opentelemetry.io/docs/specs/semconv/resource/` (Mixed resource doc; telemetry.sdk Stable)
- `https://betterstack.com/community/guides/observability/opentelemetry-semantic-conventions/` (OTEL_SEMCONV_STABILITY_OPT_IN, http/dup)
- `https://uptrace.dev/opentelemetry/semconv` (mixed semconv renames, Development gen_ai split)
- No collectors, telemetry backends, containers, network traces, SDK installs, or benchmarks were used; all evidence is synthetic and deterministic.

## Result snapshot (actual, 2026-09-18)

Fixture classifications (evaluator `results.json` / `RESULTS.md`):

```
10 cases · 15 tests OK — python3 -m unittest tests/test_stability_boundary.py -v
No overall_compliant/production_safe field emitted (intentionally withheld).
```

Stability summary:

```
Stable API (trace):      stable_major_bump_required, compatible across minor versions
Development (profiling): no_stable_guarantee, breaking changes MAY occur
API 1.24.0 vs SDK 1.31.0: independent version numbers (in same language)
Python 1.24.0 vs Java 1.32.1: languages have independent version numbers
Stable http group + Development OptIn attr: attr remains Development (group does not confer)
Contrib 0.50b1 vs Core Stable: weaker guarantee, independent versioning
Mixed semconv:           mixed_no_uniform_guarantee (Stable + Development coexist)
Manual:                  valid, automatic is one mechanism not required
Backend UI rendering:    not standardized by client-spec compatibility
```

## License

MIT
