---
name: P03-claim-submission-cycle
description: "Swarm deployment: gate-green package to payer-acknowledged submission. Agents 07, 02, 12, 13. Submitted means both artifacts - clearinghouse accept AND payer accept; the send log proves nothing."
---

# Playbook P03 - Claim Submission Cycle

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.2 (ratified 2026-07-18; extended & ratified 2026-07-18 - owner sign-off)

## Trigger
`scrub.result` at 07.

## Preconditions
- Package carries its edit-table version and green gates; timely-filing clock is live via 12.
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Phase 1 - Submit and confirm
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 07 | Submit; capture the clearinghouse acceptance artifact | `claim.submit` → external | clearinghouse accept on record |
| 2 | 07 | Confirm payer acceptance; chase at lead-time if silent | `claim.status` → 10, 13 | payer accept artifact on record - only now is it submitted |

### Phase 2 - Rejections
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 3 | 07 | Route rejections with codes verbatim; no local fixes | `rejection.notice` → 02, 13 | rejection re-enters through a fresh scrub |

## HITL gates (hard stops)
- No resubmission without a new scrub version - the duplicate-billing line.
- Timely-filing-critical claims escalate on any gate conflict; the clock never overrides a gate.

## Completion criteria
Payer acceptance artifact on record; status tracking handed to A/R follow-up.

## Abort paths
- Payer acknowledgment absent past lead-time: claim is NOT submitted; escalation with the chase history.
