---
name: P02-prior-auth-cycle
description: "Swarm deployment: auth-required service to human-attested submission and tracked outcome. Agents 06, 03, 05, 04, 12, 13. Medical necessity is clinical - packages carry provider documentation, never swarm-authored argument."
---

# Playbook P02 - Prior Authorization Cycle

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.1 (ratified 2026-07-11 - owner sign-off; not runtime-hardened)

## Trigger
`auth.request` at 06 from intake or scrubbing.

## Preconditions
- The payer rule table confirms the requirement (or the discrepancy tuple routed it here as required).
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Phase 1 - Package
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 03 | Coverage facts for auth routing | `eligibility.result` → 06, 13 | payer and plan facts attached |
| 2 | 05 | Clinical documentation per the auth checklist (sealed) | `doc.received` → 06, 13 | custody references attached, content sealed |
| 3 | 06 | Assemble the package: demographics, provider-entered codes, sealed docs | `auth.package` → human, 13 | package delivered for clinical attestation - the human signs and submits |

### Phase 2 - Track
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 4 | 06 | Chase status per cadence; report outcome facts | `auth.status` → 02, 12, 13 | auth number, valid dates, unit limits on record |
| 5 | 06 | Patient status notices on approved templates | `patient.message.request` → 04 | sends logged |
| 6 | 12 | Validity window and expiry clocks armed | (clock instantiation) | expiry alerts at lead-time |

## HITL gates (hard stops)
- No submission without the human's clinical attestation - the package waits, the swarm never signs.
- Peer-to-peer requests route to the human immediately; the swarm never voices medical necessity.

## Completion criteria
Auth outcome facts on record with validity clocks armed; the gated service's claim path unblocked or the denial routed.

## Abort paths
- Auth denied: facts to 02 and human; appeal consideration follows the denial path with a human decision.
- Pended past the service-date lead-time: escalation with the pend reason verbatim; the human decides the service-day call.
