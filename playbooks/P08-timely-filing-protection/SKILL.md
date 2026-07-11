---
name: P08-timely-filing-protection
description: "Swarm deployment: the filing-clock engine end to end - every claim's window tracked, at-risk claims surfaced at lead-time, certain misses escalated before they land. Agents 12, 07, 10, 14, 13. Clocks are facts; conservatism is ratified."
---

# Playbook P08 - Timely Filing Protection

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.1 (DRAFT - not implemented)

## Trigger
Continuous: clock instantiation on every claim path; alerts at ratified lead-times.

## Preconditions
- The payer rule table (filing limits per payer/plan) is the owner-ratified current version.
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Continuous - the clock engine
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 12 | Instantiate filing clocks per payer on every claim; disputed dates run from the earlier | (clock set) | every claim carries its window |
| 2 | 12 | Fire alerts at lead-times to the owners of the next action | `deadline.alert` → 07, 09, 10, 14 | alerts logged with lead-time basis |
| 3 | 07 | At-risk claims surface for priority handling; gate conflicts escalate | (priority handling) | no clock ever overrides a gate |
| 4 | 14 | Clock reconciliation into the books: satisfied, at-risk, missed - misses quantified | (book sections) | misses named with owners, never buried |

## HITL gates (hard stops)
- A certain miss is escalated the moment it is certain - early-reported certainty is compliance, late discovery is failure.
- Clocks are never rescheduled to fit workload.

## Completion criteria
Continuous playbook: every active claim carries a live window; the books carry the reconciliation.

## Abort paths
- Rule-table gap for a payer: the clock runs on the most conservative known limit and the gap escalates for ratification.
