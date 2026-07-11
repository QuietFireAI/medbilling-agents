---
name: P01-charge-to-clean-claim
description: "Swarm deployment: provider-documented encounter to gate-green claim package. Agents 01, 02, 03, 06, 05, 13. Coding judgment exits to the certified human at every crossing - the swarm checks rules, it never codes."
---

# Playbook P01 - Charge to Clean Claim

**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)
**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)
**Version:** 0.1 (DRAFT - not implemented)

## Trigger
`encounter.captured` lands at 02 from the intake feed.

## Preconditions
- Encounter carries provenance per field; provider-entered codes untouched (01's capture rule).
- Edit tables and payer rule table are the owner-ratified current versions.
Precondition unmet = playbook does not start; `clarification.request` to human.

## Deployment sequence

### Phase 1 - Gates (parallel)
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 1 | 03 | Verify eligibility on DOS from live payer systems | `eligibility.result` → 02, 13 | coverage facts with payer-system timestamps |
| 2 | 06 | Confirm auth requirement per rule table; auth path fires if required | `auth.status` → 02, 12, 13 | auth gate state on record with rule citation |

### Phase 2 - Scrub
| Step | Agent | Action | Intent | Proof of done |
|---|---|---|---|---|
| 3 | 02 | Run edit tables; mechanical fixes cite sources; judgment hits exit | `scrub.exception` → human, 13 (as needed) | every hit carries its rule citation |
| 4 | 05 | Collect documentation an edit requires (sealed custody) | `doc.received` → 02, 13 | inventory current, content sealed |
| 5 | 02 | Release the gate-green package | `scrub.result` → 07, 13 | package with edit-table version recorded |

## HITL gates (hard stops)
- No release with any gate amber - eligibility unknown, auth pending, or an unresolved exception all hold the claim.
- Provider-entered codes are never altered anywhere in this playbook - exceptions carry them verbatim to the human.

## Completion criteria
Gate-green claim package released to submission with eligibility, auth, and scrub citations on record.

## Abort paths
- Eligibility unknown (payer system down): claim holds; the outage is named on the record.
- Judgment-required edit unresolved: claim holds at the exception; the human's resolution re-enters through a fresh scrub.
