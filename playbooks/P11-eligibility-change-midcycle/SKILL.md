---
name: P11-eligibility-change-midcycle
description: "Swarm deployment: detected coverage change to re-opened gates on every affected claim. Agents 03, 07, 10, 02, 13. A coverage change re-opens gates going forward - it never rewrites posted history."
---

# Playbook P11 - Eligibility Change Mid-Cycle

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.1 (ratified 2026-07-11 - owner sign-off; not runtime-hardened)

## Trigger
`eligibility.result` at 03 (re-verify or payer notice) differing from the coverage facts a claim was gated on.

## Preconditions
- The prior eligibility facts are on record with timestamps - a change is only a change against a recorded baseline.
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Phase 1 - Blast radius
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 03 | Report the change with both fact sets and timestamps | `eligibility.result` → 02, 07, 10, 13 | old and new coverage facts on record |
| 2 | 13 | Return every claim gated on the prior facts | `record.response` → 07, 10 | affected-claim list with gate citations |

### Phase 2 - Re-gate
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 3 | 07 | Hold unsubmitted affected claims at the gate | (hold; `agent.status` → 14 while waiting) | held claims named with reason |
| 4 | 02 | Re-scrub held claims against corrected coverage | `scrub.result` → 07, 13 | fresh gate state per claim |
| 5 | 10 | Re-anchor in-flight follow-up to corrected facts | `payer.status` → 12, 13 | follow-up record cites the change |

## HITL gates (hard stops)
- No affected claim submits on the stale gate - re-verification precedes release, every time.
- Posted history is never edited to match new coverage - the change is recorded forward only.

## Completion criteria
Every affected claim either re-gated green on corrected facts or held with its reason named; the change and its blast radius on record.

## Abort paths
- Payer systems down for re-verify: affected claims hold; the outage is named (03's outage tuple governs).
- Change implies retroactive termination: human notified with the full record - retro-term disputes are human/payer conversations.
