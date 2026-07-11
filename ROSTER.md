# DispatcherAgents Medical Billing Swarm (Healthcare RCM) - Roster v0.1 (ratified 2026-07-11 - owner sign-off)

15 agents, hub-and-spoke via 00. All inter-agent communication is a logged
envelope through the Dispatcher; the route-space is closed (identity/routes.json).

| # | Agent | Type | Autonomy boundary |
|---|---|---|---|
| 00 | Dispatcher | Hub (transport, gates, audit) | Validates every (from, intent, to) tuple; holds ambiguity; owns the audit log |
| 01 | Encounter Intake Agent | Intake (charge capture) | Autonomous charge-capture intake and completeness checks; NEVER assigns or changes a code - coding judgment is certified-human territory |
| 02 | Claim Scrubbing Agent | Rules engine (claim edits) | Autonomous rule-table edits (format, completeness, payer-specific requirements); ANY edit requiring coding judgment routes to the certified human - the scrubber checks rules, it never practices coding |
| 03 | Eligibility Verification Agent | Systems lookup (coverage facts) | Autonomous eligibility and benefits lookups; reports payer-system facts with timestamps - never coverage promises, never patient-liability guarantees |
| 04 | Patient Communication Agent | Communication hub (patient-facing) | Autonomous sends from approved templates; NO clinical content, no collection pressure beyond the published sequence, no hardship decisions |
| 05 | Documentation Collection Agent | Evidence pipeline (clinical documentation custody) | Autonomous request, receipt, inventory, and chase per cadence; clinical CONTENT is sealed custody - the swarm inventories existence and routes, it never reads or summarizes clinical records |
| 06 | Prior Authorization Agent | Coordination (auth lifecycle) | Autonomous auth-requirement checks, package assembly, submission tracking, and status reporting; clinical attestations and peer-to-peer scheduling are human - the swarm never states medical necessity |
| 07 | Claim Submission Agent | Systems execution (clearinghouse) | Autonomous submission of gate-green claims and rejection handling; a claim submits once per scrub version - resubmission without a new scrub is the named duplicate-billing vector |
| 08 | Payment Posting Agent | Financial records (remits, adjustments) | Autonomous ERA/EOB posting per remit facts and contract-rule adjustments; ANY write-off or adjustment beyond contract rules executes only on signed human `writeoff.authority` |
| 09 | Denial Management Agent | Recovery preparation (denials, appeals) | Autonomous denial triage per the ratified reason taxonomy and appeal-package assembly; the appeal DECISION, clinical argument, and signature are human |
| 10 | A/R Follow-up Agent | Pipeline chase (accounts receivable) | Autonomous status chasing per the aging cadence and published patient-contact sequence; settlements, hardship, and collection-agency referrals are human decisions |
| 11 | Patient Billing Records Agent | Financial records (patient balances, plans) | Autonomous statement records and payment plans WITHIN published policy; plan exceptions, discounts, and hardship arrangements execute only on signed human `plan.authority` |
| 12 | Compliance & Deadlines Agent | Regulatory engine (filing clocks, payer rules) | Autonomous clock tracking and alerting; payer rule-table changes and any external response are human-ratified/signed |
| 13 | Billing Records Agent | System of record (billing file, audit) | Autonomous record keeping; the record is append-only - corrections are new entries referencing what they correct; clinical custody flags are absolute (HIPAA) |
| 14 | Daily Operations Agent | Operations cadence (books) | Autonomous book assembly and presentation; the human reads the book and directs - the book never self-executes its recommendations |

Human lanes (never automated): all coding judgment (certified coder), clinical statements and medical-necessity argument, appeal decisions and signatures, write-offs and adjustments beyond contract rules (signed authority), payment-plan exceptions and hardship arrangements, collection referrals, anything touching sealed clinical content (HIPAA custody), payer/regulator submissions.
