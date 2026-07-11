#!/usr/bin/env python3
"""Generate the meta pre-decision layer: per-agent DECISIONS.md (tuple layer)
and SWARM.md (framework manifest + swarm-level tuples).
Tuples are (crossing, answer): the deliberation happened before the run."""
import os
from generate_skills import ROUTES, AGENTS

PKG = os.path.dirname(os.path.abspath(__file__))

SWARM_TUPLES = [
 ("two playbooks match one trigger", "run neither; clarification.request naming both"),
 ("a playbook step conflicts with an agent's legal line", "halt playbook; integrity.violation - spec defect, never a judgment call"),
 ("workload exceeds capacity", "priority order: escalations > active-transaction deadlines > client-facing requests > internal/marketing > discovery; ties go to the older item"),
 ("signed human instruction conflicts with a playbook", "signed human wins; deviation logged in the after-action report"),
 ("required data is stale beyond threshold", "regenerate; never present stale as current"),
 ("one parallel step fails mid-phase", "complete independent siblings; hold dependents; flag - never abandon the phase silently"),
 ("identical envelope arrives twice", "process once; envelope_id is the idempotency key"),
 ("uncertainty about whether a legal line is crossed", "treat as crossed; escalate"),
 ("no suitable tuple exists for the task at hand", "STOP; clarification.request to the human and wait - a missing tuple is a design omission to fix, never a license to improvise"),
 ("context fade suspected or long run", "re-read MANNERS.md and own SKILL.md before the next action"),
 ("visibility limited but the path seems clear", "proceed only within stopping distance: reversible increments; irreversible or client-visible actions wait for full verified authority"),
 ("two runs contend for the same agent", "higher priority class proceeds; the lower takes the siding - held live on route, resumes when the segment clears; contention never aborts a run"),
 ("task requires a path outside declared edges", "refuse; clarification.request - an undeclared path is ambiguity, not opportunity"),
 ("an unlisted crossing is reached", "ambiguity protocol; propose the missing tuple in the after-action report for human ratification"),
]

D = {
"00": [
 ("route valid but ambiguous", "hold in clarification queue; never route on 'most likely'"),
 ("signature invalid on authority intent", "reject + integrity.violation; notify human out-of-band"),
 ("duplicate envelope_id arrives", "re-ack the original outcome; never process twice"),
 ("compliance.hold received mid-run", "suspend the named account's traffic; only 12's release or human direction resumes it"),
 ("a spoke reports done without its artifact", "treat as not-done; the artifact is the proof"),
],
"01": [
 ("provider-entered code conflicts with the service description", "route to the human coder verbatim; never reconcile at intake"),
 ("same encounter arrives from two sources with different units", "capture both with sources; the human resolves - units are money"),
 ("superbill illegible on a required field", "field unknown, encounter incomplete; never infer from billing history"),
 ("encounter arrives for a provider not in the roster", "hold; clarification - an unrostered provider is a credentialing question, not a typo"),
],
"02": [
 ("edit table update lands mid-scrub", "the version at scrub-open governs that claim; version recorded"),
 ("two edits conflict", "scrub.exception with both citations; conflicting rules are a human/payer question"),
 ("claim clean but auth gate pending", "hold; a clean claim without its auth is a denial being mailed"),
 ("a mechanical fix has two candidate source records", "no fix; exception with both - two sources is judgment"),
],
"03": [
 ("payer system down at verification", "answer unknown with the outage named; unknown blocks gates"),
 ("two payers both show active (COB)", "report both with effective dates; primacy per COB table or human"),
 ("portal and 271 disagree on benefits", "report both with timestamps; the discrepancy is the fact"),
 ("verification requested for a future DOS beyond payer window", "report the window limit; never extrapolate coverage forward"),
],
"04": [
 ("patient disputes a charge as 'never happened'", "route verbatim to human with the posted record; never argue at the patient"),
 ("inability-to-pay mentioned alongside a question", "answer from posted facts AND route the hardship verbatim; both, always"),
 ("merge amount differs from current posted balance", "hold the send; stale amounts in patient messages are the named failure"),
 ("patient reply contains clinical questions", "human queue verbatim; billing voice never answers clinical"),
],
"05": [
 ("document type unidentifiable without reading content", "inventory type-unknown, route to human; identification never excuses reading"),
 ("provider states a requested document doesn't exist", "record verbatim; absence reported, never papered over"),
 ("document arrives for the wrong patient", "sealed misdirect protocol: human immediately, event logged - HIPAA incident, not filing error"),
 ("chase cadence exhausted with items outstanding", "escalate with the chase history; the cadence ends in a human decision"),
],
"06": [
 ("rule table and payer portal disagree on auth requirement", "treat as required, route the discrepancy; the expensive assumption is the safe one"),
 ("auth approved for fewer units than scheduled", "report the limit to 02 and human; never split services to fit an auth"),
 ("service date approaching with auth pended", "escalate at lead-time with the pend reason verbatim"),
 ("payer requests clinical justification by phone", "route to human; the swarm never voices medical necessity"),
],
"07": [
 ("clearinghouse accepts, payer ack never arrives", "NOT submitted; chase the artifact, escalate at lead-time"),
 ("timely-filing-critical claim has an amber gate", "escalate immediately; the clock never overrides a gate"),
 ("same claim twice in the queue", "submit once; idempotency is the financial-safety rule"),
 ("payer portal offers a 'quick correct' on a rejection", "decline; corrections go back through a fresh scrub, always"),
],
"08": [
 ("remit adjustment code has no loaded contract rule", "post payment, hold adjustment unapplied, flag; unruled is not contractual"),
 ("payer pays differently than the contract computes", "post as paid, variance to 12; never adjust the difference away"),
 ("same remit file arrives twice", "post once; remit reference is the idempotency key"),
 ("signed write-off references a balance that changed since signing", "hold and re-confirm naming both states"),
],
"09": [
 ("denial fits two taxonomy categories", "triage to the shorter appeal clock; conservatism decides ties"),
 ("denial reason contradicts the posted auth", "package both facts for human; payer errors are argued by humans with the record"),
 ("appeal deadline passes awaiting human decision", "record the miss with its timeline; named in the books, never buried"),
 ("payer 'reprocessing' claim sits past its promise date", "payer.status fact + escalate; a promise is not a payment"),
],
"10": [
 ("payer rep states a payment date verbally", "record as stated-by-payer with rep reference; a stated date is not a posted payment"),
 ("balance under the small-balance threshold", "published rule executes via the policy path; below-threshold is not quietly ignore"),
 ("published sequence ends unresolved", "human with full contact history; the sequence ends in a decision, not an invented next step"),
 ("patient reply promises payment 'next week'", "record verbatim, sequence pauses per rule; a promise pauses per policy, never indefinitely"),
],
"11": [
 ("patient overpays", "record the credit, route refund question to human; patient refunds are never auto-issued"),
 ("plan request one month beyond published terms", "record verbatim, route to human; 'close to policy' is not policy"),
 ("posted balance changes while a statement is queued", "regenerate against the current record"),
 ("plan payment missed once", "published sequence via 10; consequences are the sequence's, never improvised"),
],
"12": [
 ("two payer rules plausibly govern a filing clock", "run both; the shorter alerts - conservatism ratified"),
 ("claim event date disputed", "earlier date runs the clock"),
 ("a miss is certain regardless of action", "escalate immediately, quantified; early certainty is compliance"),
 ("payer announces a rule change not yet ratified into the table", "alert human with the delta; the table changes only by ratification"),
],
"13": [
 ("two entries conflict on a material fact", "both stand; conflict flagged to the requester"),
 ("request would expose sealed clinical custody", "refuse with the seal named; the flag governs regardless of requester"),
 ("retention rule conflicts with an open appeal or audit", "the hold wins; escalate"),
 ("storage write unconfirmed", "not done until re-verified; unconfirmed is reported failed"),
],
"14": [
 ("book source unavailable at assembly", "section marked absent; never backfilled from yesterday"),
 ("EOD sweep finds an untouched morning item", "miss named with its owner; the sweep never reassigns"),
 ("human unreachable at book time", "publish to the queue and hold; books never expire silently"),
 ("denial volume spikes against baseline", "the spike is a named book fact with the payer breakdown; root cause is human territory"),
],
}

def decisions_md(num, name):
    rows = "\n".join(f"- ({c}, {a})" for c, a in D[num])
    rows += "\n\n(Root rule, restated: no suitable tuple - or an uncertain match - means STOP and ask the human.)"
    return f"""# Agent {num} - Predeliberated Decisions (Tuple Layer) v0.1 DRAFT

PRE-TEXT - ROOT OF THE TUPLE DECISION TREE (owner rule, binding):
before ANY task or decision, consult this layer. If NO suitable tuple covers
the task: STOP. Contact the human via clarification.request and wait. Do not
improvise, do not pick the nearest tuple, do not proceed on judgment - a
missing tuple is a design omission to be fixed, never a license to act. A
PARTIAL OR UNCERTAIN MATCH IS NOT-FOUND: if it takes judgment to decide the
tuple fits, it does not fit - STOP applies. The after-action proposes the
missing tuple so the omission is closed.

Meta pre-decision layer, above playbooks: crossings this agent may reach,
already deliberated. Format: (crossing, answer) - a location with its answer,
stored before the run. Swarm-wide tuples in /SWARM.md apply first; MANNERS.md
constrains everything.

{rows}
"""

def swarm_md():
    agents_list = "\n".join(f"- {a['num']} {a['name']}" for a in AGENTS)
    intents = sorted({i for i, *_ in ROUTES})
    tuples = "\n".join(f"- ({c}, {a})" for c, a in SWARM_TUPLES)
    return f"""# SWARM.md - Framework Manifest + Swarm-Level Decisions (v0.1 DRAFT)

Framework context for the dispatcher and every agent: as much predefined
structure as exists, until learning (after-action dataset) takes over.
MANIFEST SECTION IS MACHINE-GENERATED from ROUTES/AGENTS in generate_skills.py
 -  regenerate via gen_meta.py; hand-edits here will be overwritten and are a
defect, not a change.

## Manifest (generated)
- Agents: {len(AGENTS)+1} (00-dispatcher + {len(AGENTS)} spokes)
- Routes: {len(ROUTES)} entries, {len(intents)} distinct intents
- Playbooks: P01-P10 (playbooks/)
- Layer stack: MANNERS.md → DISPATCHER_CORE.md → identity/ → DECISIONS.md
  (per agent) → playbooks/ → agent SKILL.md files
- Track principle: the ROUTE-SPACE IS CLOSED. Agents run on predetermined
  track; an option absent from the routing table, playbooks, and tuples does
  not exist. Trains request routes; only the hub lines switches. Content-space
  is BOUNDED (manners, compliance verdicts) but not closed - generative freight
  is why inspection exists (02's rule-citation discipline, verify_swarm, after-action).
- Routes never originate on the train: a run = a FIXED route + VARIABLE events
  (scheduled work at the stations along the line, or unforeseen events that
  trigger the restricted-speed doctrine). Agents never create routes or work
  assignments; on arrival they produce documents and evaluations from
  predetermined possibilities, autonomously, under dispatcher permission.
- Crew principle: the track cannot disobey and the train cannot disobey - the
  CREW can, and derailments are crew decisions on compliant hardware. In this
  swarm the model is the crew, not the train. Rulebooks alone never stopped
  crew-caused derailments; automated enforcement did. Every rule therefore
  ships with its enforcement twin: instruction < detection (verify_swarm,
  after-action, audit log) < structural impossibility (acks, signatures,
  closed routes). Constraint reduces variance, not bias - a wrong tuple makes
  the swarm consistently wrong, which is why spec ratification outranks spec
  volume.
- Shared-segment principle: spokes are shared track segments - concurrent runs
  (trains) traverse the same agents. The dispatcher's value concentrates where
  track is shared: sequencing, priority class, and context isolation are block
  protection for segments used by other trains.
- Spokes:
{agents_list}
- Intents: {", ".join(f"`{i}`" for i in intents)}

## Swarm-level decision tuples (predictable scenarios, pre-deliberated)
{tuples}

Status: v0.1 DRAFT - manifest verified against generator data at generation
time; not runtime-tested.
"""

def main():
    # dispatcher decisions live in its folder like every spoke's
    names = {a["num"]: a["name"] for a in AGENTS}
    names["00"] = "Dispatcher"
    slugs = {a["num"]: f'{a["num"]}-{a["slug"]}' for a in AGENTS}
    slugs["00"] = "00-dispatcher"
    for num in sorted(D):
        path = os.path.join(PKG, slugs[num], "DECISIONS.md")
        open(path, "w").write(decisions_md(num, names[num]))
    open(os.path.join(PKG, "SWARM.md"), "w").write(swarm_md())
    print(f"wrote {len(D)} DECISIONS.md + SWARM.md")

if __name__ == "__main__":
    main()
