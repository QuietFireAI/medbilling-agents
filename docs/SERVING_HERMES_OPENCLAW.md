# Serving Hermes / OpenClaw - Mounting Contract

The stack rounds out three ways to run this identity:

1. **dispatcher-agents** (reference) - the vendored core in `dispatcher/`
   IS that runtime; nothing to mount, it ships here and the 24-test suite
   proves it.
2. **Hermes** - mount as a governed skill/persona per the contract below.
3. **OpenClaw** - mount as a skill folder per the contract below.

The identity is runtime-agnostic by design: routes, playbooks, tuples,
and config are data; the five absolute lines are doctrine any compliant
runtime can enforce. What follows is the honest division of labor.

---

## What the host runtime MUST provide (or must not claim compliance)

| Requirement | Reference implementation | Why it's non-optional |
|---|---|---|
| **Closed-track enforcement** - reject any (sender, intent, receiver) not in `identity/routes.json`; rejection is logged, never silent | `dispatcher/hub.py` + `core.Routes` | The track is the law; an unenforced track is decoration |
| **Append-only, hash-chained audit sink** with independent verification | `core.AuditLog` (SHA-256 prev/entry linkage, GENESIS anchor, `verify_chain()` names violations by line) | "Not trust us - check us" is the product |
| **Ed25519 signature verification on every authority intent** (`*.authority`, `config.update`), fail-closed on unsigned/invalid | `dispatcher/signatures.py` + hub enforcement | Absolute line 3; a name string is not a credential |
| **Fail-closed config loading** - UNRATIFIED `_status` refuses to arm | `dispatcher/loader.py` + `signer_registry.py` | Absence of the expected artifact means human review, never silent-admit |
| **Dead-letter + clarification queues** visible to the operator | hub queues | Ambiguity is held, never dropped |
| **A clock layer** able to call the daily sweep | `Spoke12ComplianceDeadlines.run_daily()` pattern | Line 5: clocks alert and escalate, or the runtime is negligent by design |

## What this identity provides

- `identity/routes.json` - the complete legal surface (44 routes, v0.2)
- `identity/priority.json` - contention classes (P13 credit/refund is
  class 1: the 60-day federal clock)
- `playbooks/P01-P14/SKILL.md` - fourteen mountable skills, each
  self-describing (trigger, phases, gates, aborts). OpenClaw-style
  skill-folder layout: point your skills directory at `playbooks/` and
  the root `SKILL.md` for the identity itself.
- `config/*.json` - ratified doctrine blocks (`_doctrine`) your agent
  must honor + deployment-content entries you must fill
- Per-agent `NN-*/SKILL.md` + `DECISIONS.md` - role boundaries and 83
  predeliberated tuples; the (from, intent, to) deliberation happened
  BEFORE the run, which is the point
- `dispatcher/medbilling_spokes.py` - reference handlers; port or wrap,
  but the gates they encode (verbatim codes, sealed custody, $0.00,
  both-acks, opt-out kill, two-lane triage) are the spec, not a style

## Mounting steps (either host)

1. Point the host's skill loader at the repo root `SKILL.md` (identity)
   and `playbooks/` (the fourteen playbook skills).
2. Wire the six MUSTs above to host primitives. If any cannot be wired,
   stop - run the reference runtime instead and let the host call INTO
   it. A partially governed mount is worse than none, because it wears
   the name without the guarantees.
3. Load `config/` through a fail-closed loader. UNRATIFIED templates
   (message templates awaiting `approved_by`) must refuse to arm.
4. Replace the test-persona signer in `config/authority_signers.json`
   with a real IdP login (TOP OF LIST, TUNING_MANUAL).
5. Run the acceptance gate: the host-mounted identity must pass the same
   assertions as `tests_medbilling/` - closed track rejects an illegal
   tuple, unsigned money is refused, a one-cent variance raises an
   exception, content in a document envelope raises a HIPAA escalation,
   STOP kills the sequence, and the audit sink verifies end to end.
   **A mount that hasn't passed these is not this identity.**

## Honest status (2026-07-18)

- dispatcher-agents mount: **working and tested here** (24/24 from a
  bare clone; `tools/run_demo.py` is the live proof).
- Hermes and OpenClaw mounts: **contract-complete, not yet exercised
  against either host.** The six MUSTs are the seam; no adapter code for
  either host exists in this repo yet. That gap is named here and in
  TUNING_MANUAL's TOP OF LIST rather than papered over - the first real
  mount should update this section with its acceptance-gate results.
