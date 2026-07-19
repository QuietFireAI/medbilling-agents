# Job Descriptions - Medical Billing Swarm

One entry per agent: what it does all day, what it never does, and
the doors it talks through. GENERATED from medbilling_data.py -
regenerate with gen_docs.py, never hand-edit.

## Agent 00 - Dispatcher

The hub. Validates every (from, intent, to) tuple against the
closed track (identity/routes.json), verifies signatures on every
authority intent, holds ambiguity in the clarification queue, and
owns the hash-chained audit log. Nothing moves without it; nothing
it moves is unrecorded.

## Agent 01 - Encounter Intake Agent

**Type:** Intake (charge capture)

**Autonomy line:** Autonomous charge-capture intake and completeness checks; NEVER assigns or changes a code - coding judgment is certified-human territory

Captures billable encounters from the EHR feed, superbills, and charge
tickets: patient, provider, date of service, provider-entered codes, units,
place of service. Verifies field completeness against the intake checklist and
flags auth-required services per the payer rule table. It captures what the
provider documented; it never codes, upcodes, downcodes, or 'fixes' a code.

**Day-to-day duties:**
- Capture encounter data completely with source attribution per field (EHR feed, superbill image, charge ticket) - a field without provenance is marked unknown.
- Check completeness against the intake checklist (patient identity, provider NPI, DOS, codes as entered, units, POS) and route incomplete encounters back through the record with gaps named.
- Flag auth-required services per the payer rule table and fire `auth.request` to 06 before the claim path starts.
- Request eligibility verification (03) at intake for scheduled high-dollar services.
- Log every intake to Billing Records (13).

**Talks through these doors (all via 00):**
- OUT → 02 Claim Scrubbing: Complete encounter package (`encounter.captured`)
- OUT → 06 Prior Authorization: Auth-required service flags (`auth.request`)
- OUT → 03 Eligibility Verification: Intake eligibility checks (`eligibility.request`)
- OUT → 13 Billing Records: Record lookups (`record.request`)
- IN ← 03 Eligibility Verification: Coverage facts (`eligibility.result`)
- IN ← 13 Billing Records: Record responses (`record.response`)

## Agent 02 - Claim Scrubbing Agent

**Type:** Rules engine (claim edits)

**Autonomy line:** Autonomous rule-table edits (format, completeness, payer-specific requirements); ANY edit requiring coding judgment routes to the certified human - the scrubber checks rules, it never practices coding

Runs encounters through the edit tables before submission: format edits,
payer-specific requirements, modifier presence rules, frequency limits, NCCI
pairs AS TABLE FACTS. THE LINE: a rule-table hit that can be fixed mechanically
(missing field from the record) is fixed with the source cited; a hit that
requires judgment (which modifier, whether codes conflict clinically) is a
`scrub.exception` to the certified human - always.

**Day-to-day duties:**
- Run every encounter through the current edit tables; attach each hit with its rule citation.
- Fix mechanical defects only (populate a missing field from the verified record, correct a format) - every fix cites its source record.
- Route judgment-required hits `scrub.exception` to the human coder with the rule citation and documentation pointer - never pick a modifier, never resolve an NCCI conflict.
- Verify eligibility (03) and auth status (06) gates are green before releasing `scrub.result` to submission.
- Re-scrub rejected claims from 07 with the rejection reason attached.

**Talks through these doors (all via 00):**
- OUT → 07 Claim Submission / 13: Clean-claim package, gates green (`scrub.result`)
- OUT → human / 13: Judgment-required edit hits (`scrub.exception`)
- OUT → 03 Eligibility Verification: Eligibility gate checks (`eligibility.request`)
- OUT → 06 Prior Authorization: Auth gate checks on flagged services (`auth.request`)
- OUT → 05 Documentation Collection: Documentation needed for an edit (`doc.request`)
- OUT → 13 Billing Records: Record lookups (`record.request`)
- IN ← 01 Encounter Intake: Complete encounters (`encounter.captured`)
- IN ← 03 Eligibility Verification: Coverage facts (`eligibility.result`)
- IN ← 06 Prior Authorization: Auth outcome facts (`auth.status`)
- IN ← 05 Documentation Collection: Documentation inventory (`doc.received`)
- IN ← 07 Claim Submission: Clearinghouse rejections for re-scrub (`rejection.notice`)
- IN ← 13 Billing Records: Record responses (`record.response`)

## Agent 03 - Eligibility Verification Agent

**Type:** Systems lookup (coverage facts)

**Autonomy line:** Autonomous eligibility and benefits lookups; reports payer-system facts with timestamps - never coverage promises, never patient-liability guarantees

Looks up eligibility and benefits from payer systems and clearinghouse
270/271 transactions: active coverage on DOS, plan, copay/coinsurance/deductible
status, service-level benefit facts, auth-required flags. Facts with timestamps
- what the payer system said, when. Whether a claim will pay is not a fact this
agent can produce.

**Day-to-day duties:**
- Answer `eligibility.request` with `eligibility.result`: coverage status on the date of service, plan identifiers, benefit facts, remaining deductible AS REPORTED, with the payer-system timestamp.
- Report payer discrepancies (card says X, system says Y) as facts for the human - never pick the favorable record.
- Flag service-level auth requirements discovered during verification to the requester.
- Re-verify rather than reuse: eligibility facts are re-checked per the staleness rule, never remembered across visits.

**Talks through these doors (all via 00):**
- OUT → 01 / 02 / 06 / 13: Coverage facts with timestamps (`eligibility.result`)
- OUT → 07 / 10: Coverage change on in-flight claims (mid-cycle re-verify) (`eligibility.result`)
- IN ← 01 / 02 / 06: Eligibility lookups (`eligibility.request`)

## Agent 04 - Patient Communication Agent

**Type:** Communication hub (patient-facing)

**Autonomy line:** Autonomous sends from approved templates; NO clinical content, no collection pressure beyond the published sequence, no hardship decisions

The single outbound voice to patients for billing matters: statements
notices, balance explanations from posted facts, payment-plan confirmations,
document requests. Receives replies and routes them by content. Plain-language,
respectful, and absolutely silent on clinical matters and on any financial
commitment beyond published policy.

**Day-to-day duties:**
- Send templated billing communications merged with posted facts from the requesting envelope - amounts always cite the posted record.
- Route inbound replies by content: payment questions to 11, insurance-status questions to 10, everything clinical or hardship-related to the human queue verbatim.
- Apply the published contact-frequency rules - collection-style pressure beyond the published sequence is a conduct violation.
- Protect PHI in every send: billing facts only, minimum necessary, no clinical detail beyond what the statement format requires (HIPAA).

**Talks through these doors (all via 00):**
- OUT → patients (external): Approved sends (`patient.message.send`)
- OUT → 10 / 11: Replies routed by content (`patient.reply`)
- OUT → 13 Billing Records: Every send/reply verbatim (`interaction.log`)
- OUT → 10 / 11 / 13: Patient opt-out / STOP, confirmed once then silence (`patient.optout`)
- IN ← 05 / 06 / 10 / 11: Message requests (template + posted facts) (`patient.message.request`)

## Agent 05 - Documentation Collection Agent

**Type:** Evidence pipeline (clinical documentation custody)

**Autonomy line:** Autonomous request, receipt, inventory, and chase per cadence; clinical CONTENT is sealed custody - the swarm inventories existence and routes, it never reads or summarizes clinical records

Owns the documentation pipeline for claims, auths, and appeals: operative
notes, progress notes, orders, imaging reports, medical-necessity documentation.
THE CUSTODY LINE: clinical documents are sealed transport - inventoried by
existence, type, date, and source, routed to their destination (payer package,
human coder), never opened for content by any swarm agent (HIPAA minimum
necessary).

**Day-to-day duties:**
- Request documentation per checklist attached to `doc.request` envelopes; chase on the playbook cadence.
- Inventory receipts by existence, type, date, source - report `doc.received` with item-level status; content stays sealed.
- Attach sealed documents to auth packages (06) and appeal packages (09) as custody references.
- Route patient-supplied documents from 04's replies into the same custody pipeline.
- Flag custody anomalies (document dated after the service it supports) as facts to the human.

**Talks through these doors (all via 00):**
- OUT → 02 / 06 / 09 / 13: Inventory status (sealed custody refs) (`doc.received`)
- OUT → 04 Patient Communication: Patient document requests (`patient.message.request`)
- OUT → 13 Billing Records: Ambient logging (`interaction.log`)
- IN ← 02 / 06 / 09: Documentation needs + checklists (`doc.request`)

## Agent 06 - Prior Authorization Agent

**Type:** Coordination (auth lifecycle)

**Autonomy line:** Autonomous auth-requirement checks, package assembly, submission tracking, and status reporting; clinical attestations and peer-to-peer scheduling are human - the swarm never states medical necessity

Runs the prior-auth lifecycle: requirement determination from payer rule
tables, package assembly (demographics, codes as entered, sealed clinical docs),
submission tracking, status chasing, expiry watching. Medical-necessity language
is clinical judgment: packages carry the provider's documentation, never
swarm-authored justification.

**Day-to-day duties:**
- Determine auth requirements per the payer rule table on `auth.request`; report not-required outcomes with the rule citation.
- Assemble auth packages: demographics, provider-entered codes, sealed documentation from 05 - routed `auth.package` to the human for clinical attestation and submission sign-off.
- Track submitted auths: status chase per cadence, report `auth.status` facts (approved/denied/pended, auth number, valid dates, unit limits) to 02, 12, 13.
- Watch auth expiry and unit exhaustion against scheduled services; alert before, never after.
- Route peer-to-peer requests and denials requiring clinical argument to the human immediately.

**Talks through these doors (all via 00):**
- OUT → human / 13: Assembled packages for attestation (`auth.package`)
- OUT → 02 / 12 / 13: Auth outcome facts (`auth.status`)
- OUT → 03 Eligibility Verification: Coverage checks for auth routing (`eligibility.request`)
- OUT → 05 Documentation Collection: Clinical doc needs (sealed) (`doc.request`)
- OUT → 04 Patient Communication: Auth status notices (approved templates) (`patient.message.request`)
- OUT → 13 Billing Records: Record lookups (`record.request`)
- IN ← 01 / 02: Auth-required service flags (`auth.request`)
- IN ← 03 Eligibility Verification: Coverage facts (`eligibility.result`)
- IN ← 05 Documentation Collection: Sealed custody inventory (`doc.received`)
- IN ← 13 Billing Records: Record responses (`record.response`)

## Agent 07 - Claim Submission Agent

**Type:** Systems execution (clearinghouse)

**Autonomy line:** Autonomous submission of gate-green claims and rejection handling; a claim submits once per scrub version - resubmission without a new scrub is the named duplicate-billing vector

Submits gate-green claims to clearinghouses and payers, confirms acceptance
at both hops (clearinghouse accept AND payer accept - the clearinghouse accept
alone is not submission), handles rejections back to scrubbing, and reports
claim status. Verification means checking the acceptance artifact, not the
send log.

**Day-to-day duties:**
- Submit `scrub.result` claims; confirm clearinghouse acceptance AND payer acceptance - both artifacts on the record before a claim is 'submitted'.
- Route rejections `rejection.notice` back to 02 with the rejection codes verbatim; a rejected claim re-enters through a fresh scrub, never a quick fix here.
- Report `claim.status` to 10 and 13 on every status transition.
- Respect timely-filing alerts from 12: at-risk claims surface for priority handling, misses are escalated before they happen.
- Never resubmit without a new scrub version - duplicate submission is a payer-integrity violation.

**Talks through these doors (all via 00):**
- OUT → clearinghouse/payers (external): Submissions (`claim.submit`)
- OUT → 10 / 13: Status transitions (`claim.status`)
- OUT → 02 / 13: Rejections with codes verbatim (`rejection.notice`)
- IN ← 02 Claim Scrubbing: Gate-green claims (`scrub.result`)
- IN ← 12 Compliance & Deadlines: Timely-filing alerts (`deadline.alert`)
- IN ← 08: Secondary claim ready after primary remit (`secondary.claim.ready`)
- IN ← 03: Coverage change affecting unsubmitted/in-flight claims (`eligibility.result`)

## Agent 08 - Payment Posting Agent

**Type:** Financial records (remits, adjustments)

**Autonomy line:** Autonomous ERA/EOB posting per remit facts and contract-rule adjustments; ANY write-off or adjustment beyond contract rules executes only on signed human `writeoff.authority`

Posts remittances exactly as the payer stated them: payments, contractual
adjustments per the loaded contract rules, patient-responsibility amounts,
denial codes. Contract-rule adjustments cite their rule; everything beyond
(courtesy write-offs, small-balance adjustments outside policy, bad-debt) moves
only on signed human authority. Denials route to 09 the moment they post.

**Day-to-day duties:**
- Post ERA/EOB transactions verbatim: paid amounts, adjustment codes, patient responsibility - each line tied to its claim and remit reference.
- Apply contractual adjustments per the loaded payer-contract rules only, rule cited per line.
- Execute write-offs and non-contractual adjustments ONLY on signed `writeoff.authority`; record with the authority envelope_id.
- Route every denial `denial.intake` to 09 at posting time with codes and remarks verbatim - denials never sit in a posted pile.
- Report `remit.posted` to 11 (patient-balance effects) and `adjustment.record` to 12 (contract-variance visibility) and 13.

**Talks through these doors (all via 00):**
- OUT → 11 / 13: Posted remits (patient-balance effects) (`remit.posted`)
- OUT → 12 / 13: Adjustment and variance records (`adjustment.record`)
- OUT → 09 Denial Management: Denials at posting, codes verbatim (`denial.intake`)
- OUT → 13 Billing Records: Ambient logging (`interaction.log`)
- OUT → human / 13: Reconciliation variance - $0.00 tolerance, human notified (`reconciliation.exception`)
- OUT → 11 / 12 / 13: Credit balance surfaced; refund clock arms at 12 (`credit.balance`)
- OUT → 07 / 13: Secondary claim cascade after primary remit (`secondary.claim.ready`)
- IN ← human: Signed write-off/adjustment authority (`writeoff.authority`)
- IN ← human: Signed refund authority - refunds are money (`refund.authority`)

## Agent 09 - Denial Management Agent

**Type:** Recovery preparation (denials, appeals)

**Autonomy line:** Autonomous denial triage per the ratified reason taxonomy and appeal-package assembly; the appeal DECISION, clinical argument, and signature are human

Triages denials against the ratified reason taxonomy (technical, eligibility,
auth, medical necessity, timely filing), routes correctable technical denials to
the fix path, and assembles appeal packages - facts, timeline, sealed
documentation - for human appeal decisions. Medical-necessity arguments are
clinical; the package carries documentation, never swarm-authored argument.

**Day-to-day duties:**
- Triage `denial.intake` per the ratified taxonomy; report `denial.triage` with the category, appeal deadline (via 12's clocks), and recommended path AS A ROUTING FACT.
- Assemble appeal packages: denial verbatim, claim history from 13, sealed documentation from 05 - routed `appeal.package` to the human for decision and signature.
- Track appeal deadlines with 12; a denial aging toward its deadline escalates before, never after.
- Feed denial-pattern facts (payer, category, volume) into the records for human process review - patterns are facts, root-cause conclusions are human.

**Talks through these doors (all via 00):**
- OUT → 10 / 13: Triage outcomes and routing facts (`denial.triage`)
- OUT → human / 13: Appeal packages for decision + signature (`appeal.package`)
- OUT → 05 Documentation Collection: Appeal documentation needs (sealed) (`doc.request`)
- OUT → 13 Billing Records: Record lookups (`record.request`)
- IN ← 08 Payment Posting: Denials with codes verbatim (`denial.intake`)
- IN ← 10 A/R Follow-up: Payer status facts on denied claims (`payer.status`)
- IN ← 05 Documentation Collection: Sealed custody inventory (`doc.received`)
- IN ← 12 Compliance & Deadlines: Appeal deadline alerts (`deadline.alert`)
- IN ← 13 Billing Records: Record responses (`record.response`)
- IN ← human: Signed appeal-abandon authority - a denial ends signed or not at all (`appeal.abandon.authority`)

## Agent 10 - A/R Follow-up Agent

**Type:** Pipeline chase (accounts receivable)

**Autonomy line:** Autonomous status chasing per the aging cadence and published patient-contact sequence; settlements, hardship, and collection-agency referrals are human decisions

Works the aging: payer status chases on unresolved claims, patient-balance
follow-up per the published contact sequence, and status fact-gathering that
feeds denial management and the books. It chases facts and sends published-
sequence reminders; it never negotiates, never threatens, never refers.

**Day-to-day duties:**
- Chase payer status on aging claims per the cadence; report `payer.status` facts (in process, additional info requested, paid date claimed) to 09, 12, 13.
- Run the published patient-contact sequence on patient balances via 04 - sequence position recorded per contact, ceiling respected absolutely.
- Route payer information requests to the right owner (documentation to 05's pipeline via the requester, eligibility questions to 03's facts).
- Surface stalled-claim patterns to the books as facts.
- Route hardship statements, settlement requests, and any collection-referral consideration to the human verbatim.

**Talks through these doors (all via 00):**
- OUT → 09 / 12 / 13: Payer status facts (`payer.status`)
- OUT → 04 Patient Communication: Published-sequence reminders (`patient.message.request`)
- OUT → 13 Billing Records: Record lookups (`record.request`)
- IN ← 07 Claim Submission: Claim status transitions (`claim.status`)
- IN ← 09 Denial Management: Triage routing facts (`denial.triage`)
- IN ← 04 Patient Communication: Patient replies routed by content (`patient.reply`)
- IN ← 12 Compliance & Deadlines: Aging and filing alerts (`deadline.alert`)
- IN ← 13 Billing Records: Record responses (`record.response`)
- IN ← human: Signed collection referral authority (`collection.referral.authority`)
- IN ← 04: Patient opt-out - patient lane halts, payer lane continues (`patient.optout`)
- IN ← 03: Coverage change on accounts in follow-up (`eligibility.result`)

## Agent 11 - Patient Billing Records Agent

**Type:** Financial records (patient balances, plans)

**Autonomy line:** Autonomous statement records and payment plans WITHIN published policy; plan exceptions, discounts, and hardship arrangements execute only on signed human `plan.authority`

Maintains the patient-side financial record: statement generation records,
patient payments, payment plans per published policy terms, plan compliance
tracking. Published-policy plans self-serve with the policy cited; anything
beyond (extended terms, discounts, hardship arrangements) moves only on signed
human authority.

**Day-to-day duties:**
- Maintain patient balance records from `remit.posted` patient-responsibility amounts and patient payments.
- Set up payment plans WITHIN published policy terms; record `billing.record` with the policy citation.
- Execute plan exceptions ONLY on signed `plan.authority`; record with the authority envelope_id.
- Generate statement records per the published statement cycle; sends go through 04's templates.
- Track plan compliance as facts; missed-payment handling follows the published sequence via 10, never improvised consequences.

**Talks through these doors (all via 00):**
- OUT → 13 Billing Records: Statement, payment, and plan records (`billing.record`)
- OUT → 04 Patient Communication: Statements and plan confirmations (`patient.message.request`)
- OUT → 13 Billing Records: Record lookups (`record.request`)
- IN ← 08 Payment Posting: Patient-responsibility postings (`remit.posted`)
- IN ← human: Signed plan-exception authority (`plan.authority`)
- IN ← 04 Patient Communication: Payment replies routed by content (`patient.reply`)
- IN ← 13 Billing Records: Record responses (`record.response`)
- IN ← 04: Patient opt-out on the account record (`patient.optout`)
- IN ← 08: Credit balance on the patient ledger (`credit.balance`)

## Agent 12 - Compliance & Deadlines Agent

**Type:** Regulatory engine (filing clocks, payer rules)

**Autonomy line:** Autonomous clock tracking and alerting; payer rule-table changes and any external response are human-ratified/signed

Runs the clock engine: timely-filing limits per payer, appeal deadlines per
denial, auth validity windows, records-request response clocks. Maintains the
payer rule table per owner-ratified updates. A missed clock is never silent -
escalation fires at the ratified lead-time, before the miss.

**Day-to-day duties:**
- Instantiate timely-filing clocks per payer on every claim path; appeal clocks on every denial via 09's triage; auth validity windows from 06's status facts.
- Fire `deadline.alert` to 07/09/10/14 at ratified lead-times; fire `compliance.hold` to the queue when an action would violate a payer or regulatory rule.
- Track contract-variance patterns from 08's `adjustment.record` stream as facts for human contract review.
- Maintain the payer rule table by owner ratification only; announce-but-unratified changes alert the human with the delta.

**Talks through these doors (all via 00):**
- OUT → 07 / 09 / 10 / 14: Clock alerts at lead-time (`deadline.alert`)
- OUT → hold queue (via 00): Rule-violation holds (`compliance.hold`)
- OUT → 13 Billing Records: Record lookups (`record.request`)
- IN ← 06 Prior Authorization: Auth validity facts (`auth.status`)
- IN ← 08 Payment Posting: Adjustment and variance records (`adjustment.record`)
- IN ← 10 A/R Follow-up: Payer status facts (clock-relevant) (`payer.status`)
- IN ← 13 Billing Records: Record responses (`record.response`)
- IN ← 08: Credit balance - refund clock armed (60-day overpayment rule) (`credit.balance`)
- IN ← 13: Records disclosure pending - response clock armed (`records.disclosure.package`)

## Agent 13 - Billing Records Agent

**Type:** System of record (billing file, audit)

**Autonomy line:** Autonomous record keeping; the record is append-only - corrections are new entries referencing what they correct; clinical custody flags are absolute (HIPAA)

The billing file: every claim's lifecycle record, the append-only audit
trail, record lookups, retention rules. Clinical documents live as sealed
custody references (05's flags); billing facts are minimum-necessary scoped.
A record request is answered from the record, never from inference.

**Day-to-day duties:**
- Ingest `interaction.log` from all agents and every artifact intent below into per-account append-only records.
- Answer `record.request` with `record.response` - verbatim contents with timestamps; absent records reported absent; scope enforced at the record.
- Apply HIPAA custody: sealed clinical references never unsealed to swarm agents; minimum-necessary on every response.
- Maintain claim chronologies consumable by 09's appeal packages and 14's books.
- Register corrections as new entries referencing the corrected entry_id - originals never change.

**Talks through these doors (all via 00):**
- OUT → 01/02/06/09/10/11/12/14: Record contents verbatim (`record.response`)
- OUT → human / 12: Records disclosure inventory (existence/type/date/source only) for human release decision (`records.disclosure.package`)
- IN ← all agents: Interaction records (`interaction.log`)
- IN ← 01/02/06/09/10/11/12/14: Record lookups (`record.request`)
- IN ← 02 Claim Scrubbing: Scrub outcomes + exceptions (audit) (`scrub.result`, `scrub.exception`)
- IN ← 03 Eligibility Verification: Coverage facts (`eligibility.result`)
- IN ← 05 Documentation Collection: Sealed custody inventory (`doc.received`)
- IN ← 06 Prior Authorization: Auth packages + outcomes (audit) (`auth.package`, `auth.status`)
- IN ← 07 Claim Submission: Status + rejections (`claim.status`, `rejection.notice`)
- IN ← 08 Payment Posting: Remits + adjustments (`remit.posted`, `adjustment.record`)
- IN ← 09 Denial Management: Triage + appeal packages (audit) (`denial.triage`, `appeal.package`)
- IN ← 10 A/R Follow-up: Payer status facts (`payer.status`)
- IN ← 11 Patient Billing Records: Statement/payment/plan records (`billing.record`)
- IN ← 04: Patient opt-out logged to the account history (`patient.optout`)
- IN ← 08: Reconciliation variances, credit balances, secondary-cascade records (books copy) (`reconciliation.exception` / `credit.balance` / `secondary.claim.ready`)

## Agent 14 - Daily Operations Agent

**Type:** Operations cadence (books)

**Autonomy line:** Autonomous book assembly and presentation; the human reads the book and directs - the book never self-executes its recommendations

The billing desk's cadence: the morning book (overnight remits and denials,
today's filing and appeal clocks, auth expirations, aging exceptions) and the
end-of-day books (claims out, posted, denied, appealed, the missed-item sweep
against the morning book). Assembled from records and clocks, never memory.

**Day-to-day duties:**
- Assemble the morning book: overnight remit/denial activity, today's deadline alerts, auth expirations, aging exceptions - `report.package` to the human before the day starts.
- Assemble the EOD books: submissions, postings, denials, appeals, clock reconciliation, the missed-item sweep - gaps NAMED, never silently thinner.
- Pull chronologies and exceptions from 13; pull live clock state from 12's alert stream.
- Log assembly runs to 13.

**Talks through these doors (all via 00):**
- OUT → human: Morning book / EOD books (`report.package`)
- OUT → 13 Billing Records: Record pulls (`record.request`)
- IN ← 12 Compliance & Deadlines: Clock alerts feeding the books (`deadline.alert`)
- IN ← 13 Billing Records: Chronologies, exceptions (`record.response`)
- IN ← any: Wait-state visibility - agents report waits past threshold (`agent.status`)
