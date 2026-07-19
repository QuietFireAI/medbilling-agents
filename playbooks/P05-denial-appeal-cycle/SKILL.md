---
name: P05-denial-appeal-cycle
description: "Swarm deployment: posted denial to human-decided appeal with a complete package inside the deadline. Agents 09, 05, 12, 10, 13. The appeal decision, clinical argument, and signature are human - the swarm builds the package and watches the clock."
---

# Playbook P05 - Denial & Appeal Cycle

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.2 (ratified 2026-07-18; extended & ratified 2026-07-18 - owner sign-off)

## Trigger
`denial.intake` at 09.

## Preconditions
- Denial codes and remarks captured verbatim at posting; appeal clock instantiated from the payer rule.
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Phase 1 - Triage
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 09 | Triage per the ratified taxonomy; shorter-clock category wins ties | `denial.triage` → 10, 13 | category + appeal deadline on record |
| 2 | 12 | Appeal clock armed with lead-time alerts | `deadline.alert` → 09 (at lead-times) | clock live |

### Phase 2 - Package
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 3 | 05 | Appeal documentation per checklist (sealed custody) | `doc.received` → 09, 13 | custody references attached |
| 4 | 09 | Assemble the package: denial verbatim, claim history, sealed docs | `appeal.package` → human, 13 | package delivered inside the lead-time for human decision + signature |

## HITL gates (hard stops)
- No appeal is decided, authored (clinically), signed, or submitted by the swarm - human end to end.
- A denial never dies quietly: appeal decision or signed write-off authority, one or the other, on record.

## Completion criteria
Appeal package delivered inside the lead-time; the human decision and outcome recorded.

## Abort paths
- Deadline certain to be missed: escalation with the miss quantified before it lands; the miss is named in the books.
