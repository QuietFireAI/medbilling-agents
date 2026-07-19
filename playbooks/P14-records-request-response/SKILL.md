---
name: P14-records-request-response
description: "Swarm deployment: external records request to human-approved disclosure inside the response clock. Agents 13, 12, 05, 04, 10. Sealed custody end to end - the swarm inventories existence, a human approves every release."
---

# Playbook P14 - Records Request Response

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.2 (ratified 2026-07-18; extended & ratified 2026-07-18 - owner sign-off)

## Trigger
External records request lands: payer audit via 10, patient access request via 04.

## Preconditions
- The request is captured verbatim with its date, requester, scope, and stated deadline (or the regulatory default).
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Phase 1 - Clock and inventory
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 12 | Arm the response clock (regulatory default if none stated) | `deadline.alert` → 10, 14 (at lead-times) | clock live |
| 2 | 13 | Assemble the disclosure inventory: existence, type, date, source per item - content sealed | `records.disclosure.package` → human, 12 | inventory delivered inside lead-time |
| 3 | 05 | Flag any inventoried item in sealed clinical custody | `doc.received` → 13 (custody references) | custody status per item |

### Phase 2 - Human release
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 4 | 13 | Record the human's release decision and what was disclosed | `record.response` + `interaction.log` | disclosure record: who, what, when, under whose approval |
| 5 | 04/10 | Transmit per the human's approved scope (patient lane via 04, payer lane via 10) | `patient.message.send` / `payer.status` | transmission artifact on record |

## HITL gates (hard stops)
- No content is read, summarized, or released by the swarm - inventory is existence/type/date/source only; release is human-approved, itemized, and logged.
- Scope discipline: nothing beyond the approved item list transmits - HIPAA minimum necessary is the ceiling, not a suggestion.

## Completion criteria
Human-approved disclosure transmitted inside the clock with a complete itemized record; or refusal/clarification recorded the same way.

## Abort paths
- Request scope ambiguous or overbroad: clarification to human before any inventory work product leaves the swarm.
- Misdirected or wrong-patient material discovered during inventory: 05's sealed-misdirect protocol - human immediately, HIPAA incident logged.
