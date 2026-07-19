# What Success Means - Medical Billing Swarm

Per playbook: what completion actually delivers, what human work it
displaces, and what the human still owns. No invented metrics - where a
number would be a guess, the honest statement is the displacement itself.
The certified coder, the licensed biller, and the practice owner keep
every judgment; the swarm keeps the clocks, the records, and the grind.

---

## P01 - Charge to Clean Claim
**Delivers:** a gate-green claim package - eligibility verified with payer
timestamps, auth state confirmed, edit tables run with citations, codes
exactly as the provider entered them.
**Displaces:** the eligibility-portal round trips, the edit-check pass,
the "did anyone verify this?" archaeology before submission.
**Human still owns:** every coding judgment. A judgment-required edit
exits with the codes verbatim; the swarm has no code-writing path at all.

## P02 - Prior Authorization Cycle
**Delivers:** an auth package with the provider's documentation assembled
and the auth clock armed; the claim gate holds until the payer decides.
**Displaces:** the chase - requesting clinical support, assembling the
packet, watching the pend.
**Human still owns:** medical necessity, entirely. The package field for
swarm-authored clinical argument is hardcoded to None.

## P03 - Claim Submission Cycle
**Delivers:** submission with BOTH acceptance artifacts (clearinghouse
ack AND payer ack) before anything is called submitted; rejections
re-enter through a fresh scrub, never a portal quick-fix.
**Displaces:** the "it went out, probably" ambiguity that becomes a
timely-filing denial 90 days later.
**Human still owns:** nothing here in the happy path - and that is the
point; the discipline is the deliverable.

## P04 - Payment Posting & Reconciliation
**Delivers:** payments posted, contract-matching adjustments applied with
rule citations, unruled adjustments HELD (unruled is not contractual),
and books that reconcile to $0.00 - any variance, any amount, goes to
the human as an exception.
**Displaces:** the write-it-off-it's-small reflex that leaks revenue and
the month-end variance hunt.
**Human still owns:** every write-off and adjustment beyond loaded
contract rules - signed, or it does not happen.

## P05 - Denial & Appeal Cycle
**Delivers:** two-lane triage (technical → rework; medical-necessity/
coding/clinical → straight to the human with the packet built), appeal
clocks armed, and a guaranteed ending: human decision or signed
write-off/abandon. A denial never dies quietly.
**Displaces:** the denial that sits in a work queue until its appeal
window closes unnoticed.
**Human still owns:** the appeal decision, the clinical argument, the
signature - end to end.

## P06 - A/R Aging Follow-up
**Delivers:** payer follow-up driven by the clock layer, chase history on
the record, and clean separation of the payer lane from the patient lane.
**Displaces:** the aging report nobody worked because nobody was assigned.
**Human still owns:** settlements and collection referrals - referral
moves only on signed authority.

## P07 - Patient Billing Cycle
**Delivers:** the published sequence (statement, 30, 60, 90) run to its
ceiling and no further; opt-out kills it same turn with one confirmation;
the ceiling ends in a human decision, never an auto-referral.
**Displaces:** manual statement tracking and the accidental fifth notice.
**Human still owns:** hardship arrangements, settlements, and what
happens after the final notice - with the full history in hand.

## P08 - Timely Filing Protection
**Delivers:** filing clocks with 30-day lead alerts and 10-day
escalations (ratified 2026-07-18); certain misses escalate BEFORE they
land and are named in the books when they do.
**Displaces:** the timely-filing write-off discovered at posting.
**Human still owns:** the intervention itself - the swarm makes the miss
impossible to not-know-about, not impossible.

## P09 / P10 - Morning Operations / End-of-Day Books
**Delivers:** a morning book with every wait named (agent, age, blocking
party) and every live clock listed; an EOD sweep with owners named.
**Displaces:** the standup where nobody knows what is stuck where.
**Human still owns:** the priorities. The report informs; it does not
decide.

## P11 - Eligibility Change Mid-Cycle
**Delivers:** a coverage change detected mid-cycle re-opens gates on
every affected claim - unsubmitted claims hold, in-flight follow-up
re-anchors - and posted history is never rewritten.
**Displaces:** the claim submitted on last month's coverage facts.
**Human still owns:** retro-termination disputes - those are human/payer
conversations with the record attached.

## P12 - Secondary Claim Cascade
**Delivers:** the secondary claim fired automatically when the primary
remit posts with a secondary payer on file - through the SAME scrub and
eligibility gates as any claim, primary EOB facts verbatim.
**Displaces:** the secondary that never got billed.
**Human still owns:** the same things they own on any claim; a cascade
relaxes nothing.

## P13 - Credit Balance & Refund Compliance
**Delivers:** every credit balance surfaced at posting, visible on the
patient ledger, with the federal 60-day clock armed (class 1) - and the
refund executes only on signed authority, inside the clock or escalated
before the miss.
**Displaces:** the credit sitting silently in the ledger becoming a
reverse-false-claims exposure.
**Human still owns:** the refund signature and payee determination - the
swarm never picks a payee.

## P14 - Records Request Response
**Delivers:** an itemized disclosure inventory (existence, type, date,
source - content sealed) delivered to the human inside the response
clock, and a complete record of what was released, when, under whose
approval.
**Displaces:** the scramble when the payer audit letter arrives.
**Human still owns:** every release decision. HIPAA minimum necessary is
enforced structurally: the swarm cannot disclose content it never
carries.

---

## The honest ledger

What this swarm does not do: code, appeal, diagnose, promise coverage,
touch clinical content, move unsigned money, pressure a patient past the
published sequence, or let a clock or a denial die quietly. Every one of
those sentences is enforced in code and proven by a test in
tests_medbilling/ - run it yourself; the suite is the claim.
