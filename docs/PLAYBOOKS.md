# Playbooks P01-P14 - Medical Billing Swarm

The consolidated catalog. Full per-playbook SKILL.md files live in
playbooks/. GENERATED from medbilling_playbooks.py.

## P01 - Charge to Clean Claim

Swarm deployment: provider-documented encounter to gate-green claim package. Agents 01, 02, 03, 06, 05, 13. Coding judgment exits to the certified human at every crossing - the swarm checks rules, it never codes.

**Trigger:** `encounter.captured` lands at 02 from the intake feed.

**HITL gates (hard stops):**
- No release with any gate amber - eligibility unknown, auth pending, or an unresolved exception all hold the claim.
- Provider-entered codes are never altered anywhere in this playbook - exceptions carry them verbatim to the human.

**Done means:** Gate-green claim package released to submission with eligibility, auth, and scrub citations on record.

## P02 - Prior Authorization Cycle

Swarm deployment: auth-required service to human-attested submission and tracked outcome. Agents 06, 03, 05, 04, 12, 13. Medical necessity is clinical - packages carry provider documentation, never swarm-authored argument.

**Trigger:** `auth.request` at 06 from intake or scrubbing.

**HITL gates (hard stops):**
- No submission without the human's clinical attestation - the package waits, the swarm never signs.
- Peer-to-peer requests route to the human immediately; the swarm never voices medical necessity.

**Done means:** Auth outcome facts on record with validity clocks armed; the gated service's claim path unblocked or the denial routed.

## P03 - Claim Submission Cycle

Swarm deployment: gate-green package to payer-acknowledged submission. Agents 07, 02, 12, 13. Submitted means both artifacts - clearinghouse accept AND payer accept; the send log proves nothing.

**Trigger:** `scrub.result` at 07.

**HITL gates (hard stops):**
- No resubmission without a new scrub version - the duplicate-billing line.
- Timely-filing-critical claims escalate on any gate conflict; the clock never overrides a gate.

**Done means:** Payer acceptance artifact on record; status tracking handed to A/R follow-up.

## P04 - Payment Posting & Reconciliation

Swarm deployment: remittance to posted, reconciled, variance-visible financial records. Agents 08, 11, 12, 09, 13. Payer facts post verbatim; contract rules cite themselves; everything else needs signed authority.

**Trigger:** ERA/EOB remittance arrives at 08.

**HITL gates (hard stops):**
- Write-offs and non-contractual adjustments move only on signed `writeoff.authority` - unsigned is an integrity violation.
- A remit posted differently than the payer stated it, to balance, is the named failure.

**Done means:** Remit fully posted with citations; variances recorded; denials in the denial pipeline; patient balances current.

## P05 - Denial & Appeal Cycle

Swarm deployment: posted denial to human-decided appeal with a complete package inside the deadline. Agents 09, 05, 12, 10, 13. The appeal decision, clinical argument, and signature are human - the swarm builds the package and watches the clock.

**Trigger:** `denial.intake` at 09.

**HITL gates (hard stops):**
- No appeal is decided, authored (clinically), signed, or submitted by the swarm - human end to end.
- A denial never dies quietly: appeal decision or signed write-off authority, one or the other, on record.

**Done means:** Appeal package delivered inside the lead-time; the human decision and outcome recorded.

## P06 - A/R Aging Follow-up

Swarm deployment: aging accounts worked on cadence with facts, not pressure. Agents 10, 04, 12, 13. Payer chases produce status facts; patient contact runs the published sequence to its end - which is a human decision, never an invented next step.

**Trigger:** Aging threshold or `deadline.alert` surfaces an account at 10.

**HITL gates (hard stops):**
- No settlement, negotiation, or collection referral originates in the swarm - human decisions with the full history attached.
- Contact beyond the published sequence is a conduct violation, not persistence.

**Done means:** Accounts current-cycle worked: payer facts recorded, sequence positions advanced per rule, end-of-sequence accounts in the human queue with full history.

## P07 - Patient Billing Cycle

Swarm deployment: posted patient responsibility to statements, published-policy plans, and clean balance records. Agents 11, 04, 10, 13. Policy self-serves with its citation; everything beyond moves on signed authority.

**Trigger:** `remit.posted` lands patient-responsibility amounts at 11, or the statement cycle date arrives.

**HITL gates (hard stops):**
- Plan exceptions, discounts, and hardship arrangements execute only on signed `plan.authority`.
- Patient credits route to the human refund process - never auto-issued.

**Done means:** Statements and plans current against the posted record; exceptions in the human queue with citations.

## P08 - Timely Filing Protection

Swarm deployment: the filing-clock engine end to end - every claim's window tracked, at-risk claims surfaced at lead-time, certain misses escalated before they land. Agents 12, 07, 10, 14, 13. Clocks are facts; conservatism is ratified.

**Trigger:** Continuous: clock instantiation on every claim path; alerts at ratified lead-times.

**HITL gates (hard stops):**
- A certain miss is escalated the moment it is certain - early-reported certainty is compliance, late discovery is failure.
- Clocks are never rescheduled to fit workload.

**Done means:** Continuous playbook: every active claim carries a live window; the books carry the reconciliation.

## P09 - Morning Operations

Swarm deployment: the billing desk's morning book. Overnight remits and denials, today's filing and appeal clocks, auth expirations, aging exceptions - assembled from records for human review. Agents 14, 13, 12.

**Trigger:** Scheduled daily start (owner-configured time) or owner command.

**HITL gates (hard stops):**
- A source unavailable at assembly is a named absence - never yesterday's numbers backfilled.

**Done means:** Morning book delivered with every section sourced or marked absent.

## P10 - End-of-Day Books

Swarm deployment: the closing books. Claims out, remits posted, denials triaged, appeals packaged, clock reconciliation, the missed-item sweep. Agents 14, 13, 12. Gaps named; a clean-looking book with hidden gaps is the named failure.

**Trigger:** Scheduled day end (owner-configured time) or owner command.

**HITL gates (hard stops):**
- The sweep never reassigns - it names. Reassignment is the human's morning decision.

**Done means:** EOD books delivered; sweep complete with owners named; completion event logged.

## P11 - Eligibility Change Mid-Cycle

Swarm deployment: detected coverage change to re-opened gates on every affected claim. Agents 03, 07, 10, 02, 13. A coverage change re-opens gates going forward - it never rewrites posted history.

**Trigger:** `eligibility.result` at 03 (re-verify or payer notice) differing from the coverage facts a claim was gated on.

**HITL gates (hard stops):**
- No affected claim submits on the stale gate - re-verification precedes release, every time.
- Posted history is never edited to match new coverage - the change is recorded forward only.

**Done means:** Every affected claim either re-gated green on corrected facts or held with its reason named; the change and its blast radius on record.

## P12 - Secondary Claim Cascade

Swarm deployment: primary remit posted to secondary claim submitted through full gates. Agents 08, 07, 02, 03, 13. A cascade is a claim, not a shortcut - every gate applies again.

**Trigger:** `secondary.claim.ready` at 07: primary remit posted (08) with a secondary payer on file.

**HITL gates (hard stops):**
- The secondary claim passes the same scrub and eligibility gates as any claim - no gate is waived for a cascade.
- Primary payment facts move verbatim - never recomputed, never adjusted in transit.

**Done means:** Secondary claim submitted with both acceptance artifacts, primary facts verbatim, gates cited; or held with its blocking gate named.

## P13 - Credit Balance & Refund Compliance

Swarm deployment: surfaced credit balance to signed, executed refund inside the regulatory clock. Agents 08, 12, 11, 04, 13. Class 1: the federal 60-day overpayment rule is a filing clock with penalties.

**Trigger:** `credit.balance` at 12 (and 11, 13) from posting.

**HITL gates (hard stops):**
- No refund executes unsigned - `refund.authority` is money, same doctrine as write-offs.
- The clock never slips silently: lead-time alert, then escalation before the 60-day line, every time.

**Done means:** Refund executed on signed authority inside the clock, patient notified, books reconciled to $0.00 variance; or the miss escalated before it lands.

## P14 - Records Request Response

Swarm deployment: external records request to human-approved disclosure inside the response clock. Agents 13, 12, 05, 04, 10. Sealed custody end to end - the swarm inventories existence, a human approves every release.

**Trigger:** External records request lands: payer audit via 10, patient access request via 04.

**HITL gates (hard stops):**
- No content is read, summarized, or released by the swarm - inventory is existence/type/date/source only; release is human-approved, itemized, and logged.
- Scope discipline: nothing beyond the approved item list transmits - HIPAA minimum necessary is the ceiling, not a suggestion.

**Done means:** Human-approved disclosure transmitted inside the clock with a complete itemized record; or refusal/clarification recorded the same way.
