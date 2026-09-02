# Application Diagnostic and Validation Strategies

This document defines general strategies for building an application-specific diagnostic and validation suite from the LevelUpDiag frame.

It does not prescribe a fixed number of levels, a fixed technology stack, or a universal test sequence. Each duplicated LevelUpDiag repository should select, combine, rename, or replace these strategies according to the target application's risks and architecture.

---

## 1. Purpose

A mature diagnostics suite should answer five different questions:

1. **Can the diagnostic suite itself run correctly?**
2. **Is the target application's environment and structure valid?**
3. **Does the application behave correctly under controlled conditions?**
4. **Can the observed result be proven with sufficient evidence?**
5. **Is the collected evidence complete enough for a release or operational decision?**

These questions are related, but they are not interchangeable.

A process starting successfully does not prove that the intended outcome occurred. A successful action does not prove that the correct target was changed. A set of passing checks does not prove release readiness unless all required checks were executed under the intended campaign.

---

## 2. Distinguish the Main Activities

### 2.1 Diagnostic

A diagnostic investigates the state of the application, environment, repository, or runtime. It should explain what was observed and why a problem may exist.

Diagnostics may produce `PASS`, `WARN`, `FAIL`, `BLOCKED`, `PARTIAL`, or infrastructure/configuration outcomes.

### 2.2 Validation

Validation compares observed behavior against an explicit contract, invariant, oracle, schema, expected state, or acceptance criterion.

Validation requires a defined expectation. Without an expectation, the result is observation rather than proof.

### 2.3 Benchmark

A benchmark measures behavior under a controlled task set and environment. It is primarily comparative or quantitative.

A benchmark result is valid only when the task definitions, environment, versions, execution modes, metrics, and evidence are controlled and recorded.

### 2.4 Release certification

Release certification aggregates required evidence and applies an explicit release policy.

A release decision must prove campaign completeness. It must not infer success merely because no failing report was found.

### 2.5 Demonstration

A demonstration makes capability visible to an operator, reviewer, customer, or partner.

A demo can support understanding, but it is not automatically a validation or benchmark. Demo evidence must be kept separate from formal pass criteria unless the demo itself has a defined oracle and reproducible procedure.

---

## 3. Recommended Maturity Progression

The strongest progression moves from inexpensive, deterministic checks toward expensive, stateful, real-world evidence.

### Stage 0 — Harness integrity

Before diagnosing the target application, validate the diagnostics repository itself.

Typical checks:

- manifest parses and references existing levels;
- every active level compiles or imports safely;
- level identifiers match the manifest;
- report schemas validate;
- launchers resolve to the intended levels;
- required shared modules are available;
- configuration errors are reported distinctly;
- the suite can perform a dry run without inventing results.

A broken harness cannot certify another application.

### Stage 1 — Environment and prerequisites

Verify the execution context before running application logic.

Typical checks:

- operating system and architecture;
- runtime versions;
- required executables and libraries;
- repository and workspace paths;
- permissions and writable artifact directories;
- local configuration;
- required services, devices, browsers, databases, or external tools;
- supported environment combinations.

Missing prerequisites should normally produce `BLOCKED`, `INFRA_ERROR`, or `CONFIG_ERROR`, not an application `FAIL`.

### Stage 2 — Static integrity and contracts

Validate what can be proven without starting the full application.

Typical checks:

- syntax and compilation;
- dependency direction;
- forbidden imports;
- schema validity;
- configuration and manifest consistency;
- public API and CLI contracts;
- required files and resources;
- security-sensitive path handling;
- documentation-to-code consistency;
- generated artifact ownership;
- stale or conflicting files.

Static checks are fast and deterministic, but they cannot prove runtime behavior.

### Stage 3 — Controlled component behavior

Exercise application components with controlled inputs and test doubles.

Useful test states include:

- success;
- empty input;
- invalid input;
- malformed data;
- timeout or slow response;
- unavailable dependency;
- permission denial;
- partial result;
- cancellation;
- recovery after failure.

This stage should isolate the component under test and use explicit oracles rather than visual inspection alone.

### Stage 4 — Runtime smoke and target binding

Start the real application or a representative runtime surface and prove that the diagnostic is attached to the intended target.

Typical checks:

- process starts and remains responsive;
- CLI command executes;
- GUI window or service becomes available;
- expected route, screen, module, or endpoint is reachable;
- target process, workspace, account, document, or environment is explicitly identified;
- unrelated windows, processes, repositories, or accounts are excluded;
- runtime errors are captured.

Target binding must be explicit. A test should not act merely because a superficially similar window or service is present.

### Stage 5 — Outcome and semantic-delta proof

Do not stop at “the action was sent.” Verify that the intended state transition occurred.

A strong action-validation pattern is:

```text
capture pre-state
identify the intended action
execute or simulate the action
capture post-state
compare the observed delta with the expected delta
classify the result
preserve evidence
```

Possible oracles include:

- exit code and structured output;
- file or database state;
- schema-valid artifact;
- UI accessibility state;
- application event;
- domain invariant;
- pre-state and post-state hashes;
- evaluator result;
- reviewed expected output.

Keep `task_success` separate from `verified_success`. An action can appear to complete while failing to produce the intended result.

### Stage 6 — Drift, adversarial cases, and safe refusal

Inject realistic deviations and prove that the application or diagnostic responds safely.

Examples:

- expected target is absent;
- wrong process or window is foreground;
- modal dialog changes the interaction path;
- route or UI element moved;
- response format changed;
- data is stale;
- cached state conflicts with current state;
- command output is ambiguous;
- permissions changed;
- an unsafe action becomes reachable.

Measure at least two distinct outcomes:

- **unsafe escape:** a blocked or unverified action was performed;
- **over-refusal:** a safe and valid action was unnecessarily rejected.

For destructive, financial, external, or irreversible actions, fail-closed behavior is usually preferable when target identity or verification is uncertain.

### Stage 7 — Recovery and human governance

After detecting a recoverable problem, validate the recovery strategy rather than only the failure response.

Possible strategies:

- retry with bounded limits;
- refresh or remap the target;
- replan from the current state;
- fall back to a safer interface;
- request operator guidance;
- require explicit approval;
- stop safely and preserve a resumable state.

Human involvement should be structured. A useful approval record includes:

- action requested;
- target identity;
- expected effect;
- risk classification;
- evidence available;
- decision and decision time;
- approver identity or role;
- result after approval.

A human prompt without a clear decision contract is not a governance mechanism.

### Stage 8 — Evidence, privacy, and observability

Prove that the suite can explain what happened without leaking unnecessary information.

Recommended evidence properties:

- stable run and level identifiers;
- timestamps;
- target identity;
- inputs or input hashes;
- observed outputs;
- pre-state and post-state evidence when relevant;
- commands or actions performed;
- policy decisions;
- warnings and issues;
- artifact hashes;
- redaction status;
- known limitations.

Keep raw evidence in controlled storage when necessary. Generate a separate redacted or shareable package for external review.

Logs should support reconstruction of the decision path, not merely record that a function was called.

### Stage 9 — Reliability, performance, and reproducibility

Only measure performance after functional correctness and evidence integrity are established.

Useful measurements include:

- wall-clock time;
- CPU time;
- memory peak;
- request or model calls;
- tokens or operations;
- steps;
- retries;
- cache hits;
- local energy when a validated method is available;
- success and verified-success rates;
- variance across repeated runs.

Reproducibility requires:

- fixed application and dependency versions;
- stable task definitions;
- recorded environment identity;
- controlled seeds where applicable;
- repeat policy;
- equivalent input data;
- explicit cold, warm, cached, or uncached modes;
- documented sources of non-determinism.

Use `unknown` when a metric was not measured. Do not replace missing measurements with estimates unless the field is explicitly marked as estimated and the method is documented.

### Stage 10 — Campaign and release gate

A release campaign should be an identified, immutable or append-controlled set of required executions.

A release gate should verify:

1. the intended campaign exists;
2. all required levels are declared;
3. all required levels were executed;
4. every report belongs to the same campaign;
5. reports are current, readable, and schema-valid;
6. required artifacts exist and hashes match;
7. blocking findings are absent;
8. `SKIP`, `PARTIAL`, and `WARN` are handled by explicit policy;
9. known limitations are recorded;
10. application-specific release criteria are satisfied.

A missing required result is not a pass. It should normally produce `BLOCKED`, `FAIL`, or an explicit incomplete-campaign verdict.

### Stage 11 — External reproduction and frozen evidence

For high-confidence certification, prove that the result can be reproduced outside the primary development environment.

Useful practices:

- clean-machine or clean-environment setup;
- documented installation procedure;
- dependency lock;
- sanitized test data;
- frozen task manifest;
- frozen result bundle;
- artifact hashes;
- known limitations;
- independent operator instructions;
- separation of internal and externally shareable evidence.

A release-candidate evidence package should be stable enough that later changes are detectable.

---

## 4. Design Tests Around Risks, Not Numbers

Level numbers are useful for ordering and launch conventions, but they should not become the architecture.

Select tests from the application's actual risk model.

### Example risk domains

| Application type | High-value diagnostic domains |
|---|---|
| CLI tool | parsing, exit codes, filesystem effects, cancellation, stdout/stderr, reproducibility |
| Desktop application | startup, target window binding, accessibility tree, modal handling, focus, state transitions |
| Web application | services, routes, API contracts, browser state, authentication, dynamic UI, network failure |
| API or service | health, schemas, authorization, idempotency, retries, latency, persistence |
| Compiler or toolchain | environment, input selection, compilation, diagnostics, artifact integrity, deterministic output |
| Data pipeline | source integrity, schema drift, partial processing, retries, lineage, checkpoint recovery |
| Automation agent | target scope, action verification, drift, safe refusal, recovery, human approval, evidence privacy |

A small application may need only a few levels. A safety-critical or stateful application may need many more.

---

## 5. Define an Explicit Test Specification

Every significant diagnostic or validation level should define the following before implementation:

### Identity

- stable test or level identifier;
- name;
- version;
- owner;
- status: draft, active, deprecated, or retired.

### Purpose and scope

- question being answered;
- systems or surfaces included;
- explicit exclusions;
- risk addressed.

### Prerequisites

- required tools;
- required services;
- required data;
- required permissions;
- dependencies on prior results.

### Inputs

- task or scenario definition;
- configuration;
- environment identity;
- seed or repeat policy;
- baseline identity when applicable.

### Procedure

- setup;
- action sequence;
- cleanup;
- retry or timeout behavior;
- destructive-operation controls.

### Oracle

- expected output;
- expected state transition;
- invariant;
- schema;
- evaluator;
- approved baseline;
- human decision contract.

### Metrics

- required metrics;
- optional metrics;
- units;
- aggregation method;
- treatment of unavailable values.

### Evidence and artifacts

- report files;
- logs;
- screenshots or recordings;
- state snapshots;
- manifests;
- hashes;
- redacted package.

### Verdict rules

- pass criteria;
- failure criteria;
- blocked conditions;
- warning conditions;
- policy for partial or skipped execution.

### Claim boundary

- what the result proves;
- what it does not prove;
- known limitations;
- external publication restrictions.

A test specification is not a test result. Draft specifications must never be represented as completed evidence.

---

## 6. Evidence Manifest

A general evidence manifest may contain:

```yaml
run_id: string
campaign_id: string
suite_version: string
level_id: string
level_version: string
target_application: string
target_version: string
target_identity: string | null
environment_hash: string
mode: string
scenario_id: string | null
scenario_version: string | null
seed: integer | null
started_at: timestamp
finished_at: timestamp
verdict: PASS | WARN | FAIL | SKIP | BLOCKED | PARTIAL | ERROR | INFRA_ERROR | CONFIG_ERROR
expected_outcome: string | null
observed_outcome: string | null
pre_state_hash: string | null
post_state_hash: string | null
semantic_delta_verdict: pass | fail | ambiguous | not_applicable
verified_success: true | false | unknown
policy_decision: allowed | blocked | requires_human | requires_approval | not_applicable
artifact_hashes: []
redaction_status: not_required | raw_internal | redacted | failed
warnings: []
issues: []
known_limitations: []
claim_boundary: []
```

Not every field applies to every application. The important requirement is that the schema distinguish observed facts, decisions, unavailable data, and inferred conclusions.

---

## 7. Failure Taxonomy

Use a stable failure taxonomy so results can be compared across runs.

Recommended categories include:

```text
harness_failure
configuration_failure
environment_failure
installation_failure
service_unavailable
timeout
cancellation
input_invalid
schema_mismatch
contract_violation
target_not_found
wrong_target
permission_denied
planner_or_routing_failure
action_execution_failure
outcome_verification_failure
drift_not_detected
unsafe_action_escape
over_refusal
recovery_failure
evidence_incomplete
redaction_failure
artifact_integrity_failure
performance_budget_exceeded
reproducibility_failure
operator_confusion
claim_boundary_violation
```

Do not collapse all failures into one generic `FAIL`. The category should identify which layer owns the problem and what the operator should do next.

---

## 8. Baselines and Comparisons

A useful baseline is an explicitly identified comparison point, not simply “the previous run.”

Possible baselines include:

- current release versus previous compatible release;
- feature enabled versus disabled;
- cached versus uncached execution;
- automated versus human-guided execution;
- new implementation versus established implementation;
- expected output versus observed output;
- clean environment versus configured environment.

For paired comparisons:

- use the same task manifest;
- use equivalent inputs;
- record environment differences;
- report absolute results and deltas;
- preserve failure cases;
- include uncertainty or variance when repeated runs are used.

Do not claim general superiority from a small, selected, or non-comparable task set.

---

## 9. Safety and Non-Destructive Defaults

Diagnostics should be read-only by default whenever practical.

Potentially destructive operations include:

- deleting or overwriting data;
- sending external messages;
- submitting forms;
- making purchases or transfers;
- changing production state;
- modifying reviewed baselines;
- approving privileged actions;
- publishing artifacts externally.

When such operations are necessary, require:

1. explicit configuration or opt-in;
2. verified target identity;
3. sandbox or synthetic data where possible;
4. clear preview of the expected effect;
5. approval when policy requires it;
6. post-action verification;
7. recovery or rollback guidance;
8. complete evidence.

A safety check should verify behavior, not merely the presence of a safety-related class or configuration field.

---

## 10. Privacy and Shareable Evidence

Separate local raw evidence from shareable evidence.

Raw evidence may contain:

- local paths;
- account names;
- document content;
- screenshots;
- environment variables;
- credentials or tokens;
- internal hostnames;
- customer data.

A shareable evidence package should:

- redact or hash sensitive identifiers;
- remove secrets;
- avoid unnecessary raw screenshots;
- identify the redaction method;
- record whether redaction succeeded;
- preserve enough structure to audit the result;
- fail the external packaging step if sensitive leakage is detected.

Redaction is part of validation, not only report formatting.

---

## 11. Observability for Operators

A diagnostic suite should make the following understandable:

- what is being tested;
- which target is bound;
- what action is about to occur;
- why the action is allowed, blocked, or requires approval;
- what evidence was captured;
- whether the intended outcome was verified;
- what failed;
- what the recommended next action is.

Operator-visible summaries should remain consistent with machine-readable reports. A graphical presentation must not hide warnings, blocked prerequisites, or incomplete evidence.

---

## 12. Release Policy

Each customized suite should define its own policy for verdict aggregation.

A possible default policy is:

| Verdict | Default release treatment |
|---|---|
| `PASS` | Accept |
| `WARN` | Accept only when explicitly permitted |
| `FAIL` | Block |
| `SKIP` | Block when the check is required |
| `BLOCKED` | Block when the check is required |
| `PARTIAL` | Block unless policy explicitly accepts partial evidence |
| `ERROR` | Block |
| `INFRA_ERROR` | Block or mark campaign invalid |
| `CONFIG_ERROR` | Block or mark campaign invalid |

The release policy should also define:

- required levels;
- optional levels;
- permitted warnings;
- treatment of first-run baseline absence;
- freshness limits;
- minimum repeat count;
- artifact requirements;
- external reproduction requirements;
- known-issue exceptions;
- approval authority.

---

## 13. What to Reuse from Mature Diagnostic Progressions

The following patterns are broadly valuable:

- start with a validated harness before testing the application;
- progress from static checks to controlled runtime checks;
- bind explicitly to the intended target;
- verify post-action state rather than trusting action dispatch;
- separate task completion from verified success;
- inject drift and adverse conditions deliberately;
- measure safe refusal and over-refusal separately;
- test recovery, not only failure detection;
- include human approval and guidance as explicit contracts;
- preserve structured evidence and stable artifact hashes;
- distinguish internal raw evidence from redacted shareable evidence;
- fix versions, task manifests, seeds, and execution modes for benchmarks;
- compare equivalent cold, warm, cached, uncached, or baseline runs;
- require repeated runs before making reliability claims;
- freeze release-candidate evidence and document limitations;
- state claim boundaries so controlled results are not overstated.

These are strategies, not mandatory level names or numbering conventions.

---

## 14. Patterns to Avoid

### Treating the level number as maturity proof

A high identifier does not make a test stronger. Strength comes from the contract, oracle, execution, and evidence.

### Large monolithic level files

A level that contains hundreds of lines of duplicated configuration, filesystem, UI, hashing, reporting, and runtime helpers becomes difficult to review and reuse.

Move stable technical mechanisms into shared modules when they are genuinely common inside the customized suite.

### Repeating the same specification boilerplate

When many benchmark specifications share the same evidence schema, metrics, failure taxonomy, and claim rules, move those common rules into one normative benchmark contract and reference it from each test.

### Manual version suffixes in filenames

Names such as `UPDATED_V2` or `FINAL_V3` create ambiguity. Prefer source-control history plus explicit manifest or schema versions.

### Mixing specifications and results

A checklist, empty result stub, or planned artifact does not prove execution. Store specifications, run reports, and frozen result packages separately.

### Mixing diagnostics with business valuation

Technical evidence may inform business decisions, but financial value hypotheses should not be part of the diagnostic verdict or test maturity model.

### Allowing demos to substitute for validation

A visible demo can be useful, but it must not replace deterministic oracles, repeatability, and negative-case testing.

### Aggregating historical reports without campaign identity

Release gates must not combine stale, unrelated, or partial reports simply because they exist under the artifact directory.

### Treating skipped work as success

A required skipped test is incomplete evidence, not a pass.

---

## 15. Minimal Recommended Strategy

A small but credible application-specific suite can begin with:

```text
L00  Harness Integrity
L01  Environment and Configuration
L02  Static Integrity and Contracts
L03  Controlled Component Validation
L04  Runtime Smoke and Target Binding
L05  Outcome Verification and Error Resilience
L06  Evidence, Privacy, and Reproducibility
L07  Release Gate
```

This is only an example. Levels may be merged, split, renamed, or reordered.

The important progression is:

```text
prove the harness
prove prerequisites
prove structure
prove controlled behavior
prove real runtime behavior
prove the resulting state
prove resilience and evidence
prove campaign completeness
```

---

## 16. Review Checklist

Before accepting a new diagnostic level, ask:

- Is the purpose explicit?
- Is the target scope explicit?
- Are prerequisites separated from application failures?
- Is there a real oracle?
- Does the test verify an outcome rather than only an attempted action?
- Are negative and adverse cases included?
- Is destructive behavior disabled by default?
- Are recovery or refusal rules defined?
- Are evidence and artifacts structured?
- Are sensitive values protected?
- Can the result be reproduced?
- Are unavailable measurements recorded as unknown?
- Are pass, fail, blocked, skip, and partial conditions distinct?
- Does the test state what it does not prove?
- Can the release gate determine whether the result belongs to the intended campaign?

Before accepting a release campaign, ask:

- Were all required levels executed?
- Were they executed against the intended application version and environment?
- Are the reports schema-valid and current?
- Are required artifacts present and hash-verified?
- Were warnings, skips, blocked results, and partial evidence evaluated by policy?
- Were known limitations preserved?
- Is the decision supported by positive completeness evidence?

---

## 17. Final Principle

The central progression of a diagnostic suite is not from low level numbers to high level numbers. It is from **assumption to evidence**:

```text
configuration is declared
prerequisites are proven
behavior is exercised
outcome is verified
failure modes are challenged
recovery and safety are demonstrated
evidence is preserved
reproducibility is measured
release claims are bounded
```

A mature LevelUpDiag adaptation should make every important claim traceable to a defined test, a recorded execution, and verifiable evidence.
