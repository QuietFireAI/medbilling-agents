# TUNING_MANUAL - medbilling-agents

Every configurable parameter, placeholder, and ratification in this identity.
Rule (inherited from listing-agents doctrine): any commit introducing a tunable
updates this manual in the same commit.

---

## TOP OF LIST - Deliberate placeholders & unratified content (read before deployment)

Full sweep 2026-07-18: everything stubbed, templated, or pending sign-off is
listed here. If it's not in this table it's ratified content or real spec.

| Item | Where | Status | What blocks / what to do |
|---|---|---|---|
| Signer identity | `config/authority_signers.json` | **RATIFIED FOR TEST 2026-07-18** — "Dr. Jeff Phillips" is a fictional test persona | Valid for demo/test only. Production MUST replace `signer_login` with a real IdP login before go-live. The IdP seam (INTEGRATIONS.md) is a go-live prerequisite for any authority intent. |
| Payer contract entries | `config/contract_rules.json` | **DOCTRINE RATIFIED / entries empty** | Empty table is fail-closed by structure: nothing matches, nothing auto-posts, everything goes to signed human. Load your real payer contracts at deployment. |
| Denial category entries | `config/denial_taxonomy.json` | **DOCTRINE RATIFIED / entries deployment content** | Two-lane triage doctrine binding; refine categories against your real payer mix. |
| Payer rule table / edit tables | `config/payer_rule_table.json`, `config/edit_tables.json` | **DEPLOYMENT CONTENT** | Owner-ratified versions required before P01 runs; the version at scrub-open governs each claim. |
| Message templates | `config/message_templates.json` | **UNRATIFIED — awaiting owner sign-off per template** | Fill `approved_by` name/date per template to ratify wording. |
| Hermes / OpenClaw adapters | `docs/SERVING_HERMES_OPENCLAW.md` | **CONTRACT-COMPLETE, NOT EXERCISED** | Six-MUST mounting contract written; no adapter code for either host exists yet; first real mount records its acceptance-gate results in that doc. |
| Runtime | `dispatcher/` + `tests_medbilling/` | **WORKING BUILD (2026-07-18)** | Vendored dispatcher core + 14 real spokes; 24-test e2e suite covers every playbook P01-P14 and every absolute line; `tools/run_demo.py` runs one patient end to end. Exhaustive per-tuple coverage at listing-agents depth is the next pass - playbook paths and hard gates are implemented, the long tail of DECISIONS.md tuples is tracked, not pretended. |

---

## Ratified thresholds (owner: Jeff Phillips, 2026-07-18, approved as written)

| Parameter | Value | Consumer |
|---|---|---|
| Timely-filing alert lead time | **30 days** before payer deadline | 12 → `deadline.alert` |
| Timely-filing escalation | **10 days** before deadline | 12 → `escalation.*` |
| Appeal-clock alert lead time | **14 days** | 12 → `deadline.alert` (P05) |
| Appeal-clock escalation | **5 days** | 12 → `escalation.*` (P05) |
| Clean-claim submission SLA | **72 hours** from encounter capture | 14 morning report; 02/07 pacing |
| Eligibility re-check staleness | **30 days** | 03 re-verify trigger (P11 feed) |
| A/R follow-up trigger | **30 days** post-submission, no payer response | 10 (P06) |
| Payment-posting reconciliation tolerance | **$0.00** | 08 → `reconciliation.exception` |

### The $0.00 rule (permeates ALL identity blueprints - owner decision 2026-07-18)

Any variance between posted remit and reconciled books, any amount, is a
`reconciliation.exception` routed to the human and the books. There is no
"close enough" lane, no de-minimis write-down, no rounding absorption. The
HITL is notified on every variance. This doctrine is identity-independent
and applies to every blueprint in the catalog (listing, freight, enrollment,
hr, mortgage, property-mgmt, practice, and all future identities).

### Zero-threshold adjustment doctrine (companion rule, ratified 2026-07-18)

Contract-matching adjustments auto-post with rule citation. Everything else,
any amount, moves only on signed human authority (`writeoff.authority`,
`refund.authority`). No dollar threshold exists anywhere in the money lane.

---

## Regulatory clocks (fixed by law, not tunable - listed for completeness)

| Clock | Basis | Playbook |
|---|---|---|
| Federal 60-day overpayment refund | ACA §6402(a) reverse false claims exposure | P13 (class 1) |
| Payer timely-filing windows | per contract / payer rule table | P08 |
| Records-response deadlines | HIPAA patient access (30 days) / payer audit terms | P14 |

Lead-time alerts for these clocks derive from the ratified thresholds above
(30/10 pattern) unless the payer contract states shorter.

---

## Contact sequence (ratified 2026-07-18, `config/contact_sequence.json`)

Statement day 0 → reminder day 30 → reminder day 60 → final notice day 90 →
human decision (never auto-referral). Window 08:00-21:00 local, no Sundays,
max 1 touch per 25 days per balance. `patient.optout` kills the sequence
immediately: one confirmation, then silence; legally required notices route
to the human with the opt-out named.
