---
name: P13-credit-balance-refund
description: "Swarm deployment: surfaced credit balance to signed, executed refund inside the regulatory clock. Agents 08, 12, 11, 04, 13. Class 1: the federal 60-day overpayment rule is a filing clock with penalties."
---

# Playbook P13 - Credit Balance & Refund Compliance

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.1 (ratified 2026-07-11 - owner sign-off; not runtime-hardened)

## Trigger
`credit.balance` at 12 (and 11, 13) from posting.

## Preconditions
- The credit is computed from posted remits and payments on record - a suspected credit without posted support routes to human as a question, not a credit.
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Phase 1 - Clock and visibility
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 12 | Arm the refund clock per regulation (60-day rule where applicable); lead-time alerts set | `deadline.alert` → 10, 14 (at lead-times) | clock live with regulatory citation |
| 2 | 11 | Post the credit to the patient-facing ledger with refund status | `billing.record` → 13 | credit visible on the account |

### Phase 2 - Human decision and execution
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 3 | 08 | Package the credit: source remits, payments, computed amount, payee determination facts | `reconciliation.exception` → human, 13 | package delivered inside lead-time |
| 4 | 08 | Execute the refund on signed authority only | (await `refund.authority` ← human) | signed envelope on the chain before any money moves |
| 5 | 04 | Notify the patient from posted facts once executed | `patient.message.send` → external | templated notice, posted-facts only |

## HITL gates (hard stops)
- No refund executes unsigned - `refund.authority` is money, same doctrine as write-offs.
- The clock never slips silently: lead-time alert, then escalation before the 60-day line, every time.

## Completion criteria
Refund executed on signed authority inside the clock, patient notified, books reconciled to $0.00 variance; or the miss escalated before it lands.

## Abort paths
- Payee ambiguous (patient vs payer vs unclaimed-property): human decision with both determinations packaged - the swarm never picks a payee.
- Signed authority not received at escalation threshold: certain-miss escalation fires; the miss is named in the books (P08 doctrine).
