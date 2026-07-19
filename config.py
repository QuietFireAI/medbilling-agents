# build config: medbilling-agents
ROOT = "/home/claude/medbilling-agents"
REPO = "medbilling-agents"
BRAND = "DispatcherAgents Medical Billing Swarm (Healthcare RCM)"
SWARM_SHORT = "Medical Billing"
DOMAIN = "Healthcare RCM"
NOUN = "billing"
VERTICAL = "medical-billing-agent"
AUTH_INTENT = "writeoff.authority"
PINGPONG = "(e.g., 02\u219403 verify ping-pong on a borderline eligibility record)"
ESCALATIONS = "`escalation.coding_judgment` / `escalation.hipaa`"
INSPECTION_REF = "02's rule-citation discipline"
DATA = "medbilling_data.py"
TUPLES = "medbilling_tuples.py"
PLAYBOOKS = "medbilling_playbooks.py"
ENVELOPE_AGENT = "02-claim-scrubbing"
IDENTITY_MD = "IDENTITY-medical-billing-agent.md"
LAST_AGENT = "14-daily-operations"
LIC_NOUN = "medical-billing agent"
CLASSES = {"P01": 2, "P02": 1, "P03": 2, "P04": 2, "P05": 1,
           "P06": 3, "P07": 2, "P08": 1, "P09": 2, "P10": 2,
           "P11": 2, "P12": 2, "P13": 1, "P14": 2}
PRIORITY_DOCTRINE = ("JIT run-priority per core doctrine: class 1 = clock-critical "
 "(prior auth blocking care, appeal deadlines, timely filing), class 2 = active "
 "revenue-cycle lifecycle and books, class 3 = aging follow-up. Pacing over "
 "braking: the siding scheduler paces class contention; nothing slam-stops.")
HUMAN_LANES = ("Human lanes (never automated): all coding judgment (certified coder), "
 "clinical statements and medical-necessity argument, appeal decisions and "
 "signatures, write-offs and adjustments beyond contract rules (signed authority), "
 "payment-plan exceptions and hardship arrangements, collection referrals, "
 "anything touching sealed clinical content (HIPAA custody), payer/regulator "
 "submissions.")
DESC = '''DESC = {
 "00": "Billing swarm dispatcher. The hub: validates every (from, intent, to) tuple against the closed track, holds ambiguity in clarification, and owns the audit log. Nothing moves without it.",
 "01": "Encounter intake. Use when billable encounters need complete, source-attributed charge capture with auth-required flags - codes captured as provider-entered, never assigned or changed.",
 "02": "Claim scrubbing. Use when encounters need edit-table checks before submission - mechanical fixes cite sources; judgment-required hits exit to the certified human coder, always.",
 "03": "Eligibility verification. Use when coverage and benefit facts are needed from live payer systems with timestamps - facts only, never coverage or payment promises.",
 "04": "Patient communication. Use when patients need templated billing messages from posted facts, or replies need content-routing - no clinical content, no pressure beyond the published sequence, no hardship decisions.",
 "05": "Documentation collection. Use when clinical documentation needs requesting, sealed-custody inventory, and routing for claims, auths, and appeals - existence and routing only, content never read (HIPAA).",
 "06": "Prior authorization. Use when auth requirements need rule-table determination, package assembly for human clinical attestation, submission tracking, and expiry watching - the swarm never voices medical necessity.",
 "07": "Claim submission. Use when gate-green claims need clearinghouse submission with BOTH acceptance artifacts confirmed, rejection routing, and status reporting - resubmission only through a fresh scrub.",
 "08": "Payment posting. Use when remits need verbatim posting, contract-rule adjustments with citations, and denial routing at post time - write-offs beyond contract rules move only on SIGNED authority.",
 "09": "Denial management. Use when denials need taxonomy triage, deadline-tracked appeal packages with sealed documentation - the appeal decision, clinical argument, and signature are human.",
 "10": "A/R follow-up. Use when aging claims need payer status chases and patient balances need the published contact sequence - facts and cadence, never negotiation, threats, or referrals.",
 "11": "Patient billing records. Use when statements, patient payments, and in-policy payment plans need records with citations - exceptions execute only on SIGNED plan authority.",
 "12": "Compliance and deadlines. Use when timely-filing, appeal, and auth-validity clocks need instantiation, lead-time alerts, and rule-violation holds - clocks are facts, conservatism ratified.",
 "13": "Billing records. Use when interactions need the append-only billing file, verbatim record lookups, and chronologies - clinical custody sealed (HIPAA), minimum necessary on every response.",
 "14": "Daily operations. Use for the morning book, end-of-day books with missed-item sweep, and clock reconciliation - books inform, the human directs.",
}'''
