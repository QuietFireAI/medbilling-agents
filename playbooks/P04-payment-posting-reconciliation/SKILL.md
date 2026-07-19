---
name: P04-payment-posting-reconciliation
description: "Swarm deployment: remittance to posted, reconciled, variance-visible financial records. Agents 08, 11, 12, 09, 13. Payer facts post verbatim; contract rules cite themselves; everything else needs signed authority."
---

# Playbook P04 - Payment Posting & Reconciliation

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.2 (ratified 2026-07-18; extended & ratified 2026-07-18 - owner sign-off)

## Trigger
ERA/EOB remittance arrives at 08.

## Preconditions
- Payer contract rules loaded are the owner-ratified versions; remit reference dedupe check passes.
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Phase 1 - Post
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 08 | Post payments, contractual adjustments (rule cited per line), patient responsibility | `remit.posted` → 11, 13 | every line tied to claim + remit reference |
| 2 | 08 | Record variances against contract computation | `adjustment.record` → 12, 13 | variance facts visible, never absorbed |
| 3 | 08 | Route denials at posting time, codes verbatim | `denial.intake` → 09 | no denial sits in a posted pile |

### Phase 2 - Patient-side effects
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 4 | 11 | Update patient balances; statement cycle picks up per policy | `billing.record` → 13 | balance records current |

## HITL gates (hard stops)
- Write-offs and non-contractual adjustments move only on signed `writeoff.authority` - unsigned is an integrity violation.
- A remit posted differently than the payer stated it, to balance, is the named failure.

## Completion criteria
Remit fully posted with citations; variances recorded; denials in the denial pipeline; patient balances current.

## Abort paths
- Unruled adjustment code: payment posts, adjustment holds unapplied, human flagged.
- Authority anomaly (changed balance since signing): hold + re-confirm naming both states.
