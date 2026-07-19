---
name: P07-patient-billing-cycle
description: "Swarm deployment: posted patient responsibility to statements, published-policy plans, and clean balance records. Agents 11, 04, 10, 13. Policy self-serves with its citation; everything beyond moves on signed authority."
---

# Playbook P07 - Patient Billing Cycle

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.2 (ratified 2026-07-18; extended & ratified 2026-07-18 - owner sign-off)

## Trigger
`remit.posted` lands patient-responsibility amounts at 11, or the statement cycle date arrives.

## Preconditions
- Statement content merges only from the current posted record (11's stale-statement tuple).
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Phase 1 - Statements
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 11 | Generate statement records per the published cycle | `billing.record` → 13 | statement record with posted-balance reference |
| 2 | 04 | Statement sends on approved templates | `patient.message.send` | sends logged verbatim |

### Phase 2 - Plans
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 3 | 11 | Set up in-policy payment plans with the policy cited; exceptions route to human | `billing.record` → 13 | plan terms + citation (or authority envelope_id) on record |
| 4 | 10 | Missed-plan-payment handling per the published sequence | `patient.message.request` → 04 | sequence facts recorded; no improvised consequences |

## HITL gates (hard stops)
- Plan exceptions, discounts, and hardship arrangements execute only on signed `plan.authority`.
- Patient credits route to the human refund process - never auto-issued.

## Completion criteria
Statements and plans current against the posted record; exceptions in the human queue with citations.

## Abort paths
- Balance changes mid-cycle: queued statements regenerate against the current record before send.
