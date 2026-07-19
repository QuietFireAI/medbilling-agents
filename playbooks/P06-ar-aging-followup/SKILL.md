---
name: P06-ar-aging-followup
description: "Swarm deployment: aging accounts worked on cadence with facts, not pressure. Agents 10, 04, 12, 13. Payer chases produce status facts; patient contact runs the published sequence to its end - which is a human decision, never an invented next step."
---

# Playbook P06 - A/R Aging Follow-up

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.2 (ratified 2026-07-18; extended & ratified 2026-07-18 - owner sign-off)

## Trigger
Aging threshold or `deadline.alert` surfaces an account at 10.

## Preconditions
- The published patient-contact sequence and payer chase cadence are the ratified versions.
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Phase 1 - Payer side
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 10 | Chase payer status per cadence; record facts with rep references | `payer.status` → 09, 12, 13 | stated dates recorded as stated-by-payer, never as posted |

### Phase 2 - Patient side
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 2 | 10 | Run the published contact sequence via approved templates | `patient.message.request` → 04 | sequence position recorded per contact; ceiling absolute |
| 3 | 04 | Route replies by content; hardship verbatim to human | `patient.reply` → 10, 11 | hardship statements never absorbed into the sequence |

## HITL gates (hard stops)
- No settlement, negotiation, or collection referral originates in the swarm - human decisions with the full history attached.
- Contact beyond the published sequence is a conduct violation, not persistence.

## Completion criteria
Accounts current-cycle worked: payer facts recorded, sequence positions advanced per rule, end-of-sequence accounts in the human queue with full history.

## Abort paths
- Sequence exhausted unresolved: human queue with the complete contact history - the sequence ends in a decision.
