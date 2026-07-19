---
name: P12-secondary-claim-cascade
description: "Swarm deployment: primary remit posted to secondary claim submitted through full gates. Agents 08, 07, 02, 03, 13. A cascade is a claim, not a shortcut - every gate applies again."
---

# Playbook P12 - Secondary Claim Cascade

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.1 (ratified 2026-07-11 - owner sign-off; not runtime-hardened)

## Trigger
`secondary.claim.ready` at 07: primary remit posted (08) with a secondary payer on file.

## Preconditions
- Primary remit posted with adjustments applied per loaded contract rules (or held unapplied per 08's unruled tuple).
- Secondary payer on file from eligibility/COB facts, not assumption.
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Phase 1 - Assemble
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 08 | Package primary payment facts verbatim (paid, adjusted, patient responsibility) | `secondary.claim.ready` → 07, 13 | primary EOB facts attached verbatim |
| 2 | 03 | Confirm secondary coverage active on DOS | `eligibility.result` → 07, 13 | secondary coverage facts with timestamps |

### Phase 2 - Gate and submit
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 3 | 02 | Fresh scrub with COB edits | `scrub.result` → 07, 13 | gate-green with edit-table version |
| 4 | 07 | Submit; both acceptance artifacts confirmed | `claim.submit` → external; `claim.status` → 10, 13 | clearinghouse AND payer ack on record |

## HITL gates (hard stops)
- The secondary claim passes the same scrub and eligibility gates as any claim - no gate is waived for a cascade.
- Primary payment facts move verbatim - never recomputed, never adjusted in transit.

## Completion criteria
Secondary claim submitted with both acceptance artifacts, primary facts verbatim, gates cited; or held with its blocking gate named.

## Abort paths
- Secondary coverage cannot be confirmed: claim holds; unknown blocks gates (identity rule).
- Timely-filing clock on the secondary at risk: P08 doctrine takes over - escalate at lead-time.
