#!/usr/bin/env python3
"""Generate playbooks P01-P10 for the DispatcherAgents Medical Billing Swarm (Healthcare RCM)."""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playbooks")

def build(p):
    s = f'---\nname: {p["num"]}-{p["slug"]}\ndescription: "{p["desc"]}"\n---\n\n'
    s += f'# Playbook {p["num"]} - {p["name"]}\n\n'
    s += "**Swarm:** DispatcherAgents Medical Billing Swarm (Healthcare RCM)\n**Type:** Deployment playbook (consumed by Agent 00 - Dispatcher)\n**Version:** 0.1 (ratified 2026-07-11 - owner sign-off; not runtime-hardened)\n\n"
    s += "## Trigger\n" + p["trigger"] + "\n\n## Preconditions\n"
    for x in p["pre"]: s += f"- {x}\n"
    s += "Precondition unmet = playbook does not start; `clarification.request` to human.\n\n## Deployment sequence\n"
    for title, rows in p["phases"]:
        s += f"\n### {title}\n| Step | Agent | Action | Intent | Proof of done |\n|---|---|---|---|---|\n"
        for r in rows: s += "| " + " | ".join(r) + " |\n"
    s += "\n## HITL gates (hard stops)\n"
    for g in p["gates"]: s += f"- {g}\n"
    s += "\n## Completion criteria\n" + p["completion"] + "\n\n## Abort paths\n"
    for a in p["abort"]: s += f"- {a}\n"
    if p.get("notes"): s += "\n## Notes for the Dispatcher\n" + p["notes"] + "\n"
    return s

PB = [
 dict(num="P01", slug="charge-to-clean-claim", name="Charge to Clean Claim",
  desc="Swarm deployment: provider-documented encounter to gate-green claim package. Agents 01, 02, 03, 06, 05, 13. Coding judgment exits to the certified human at every crossing - the swarm checks rules, it never codes.",
  trigger="`encounter.captured` lands at 02 from the intake feed.",
  pre=["Encounter carries provenance per field; provider-entered codes untouched (01's capture rule).",
       "Edit tables and payer rule table are the owner-ratified current versions."],
  phases=[
   ("Phase 1 - Gates (parallel)", [
    ("1","03","Verify eligibility on DOS from live payer systems","`eligibility.result` → 02, 13","coverage facts with payer-system timestamps"),
    ("2","06","Confirm auth requirement per rule table; auth path fires if required","`auth.status` → 02, 12, 13","auth gate state on record with rule citation"),
   ]),
   ("Phase 2 - Scrub", [
    ("3","02","Run edit tables; mechanical fixes cite sources; judgment hits exit","`scrub.exception` → human, 13 (as needed)","every hit carries its rule citation"),
    ("4","05","Collect documentation an edit requires (sealed custody)","`doc.received` → 02, 13","inventory current, content sealed"),
    ("5","02","Release the gate-green package","`scrub.result` → 07, 13","package with edit-table version recorded"),
   ]),
  ],
  gates=["No release with any gate amber - eligibility unknown, auth pending, or an unresolved exception all hold the claim.",
         "Provider-entered codes are never altered anywhere in this playbook - exceptions carry them verbatim to the human."],
  completion="Gate-green claim package released to submission with eligibility, auth, and scrub citations on record.",
  abort=["Eligibility unknown (payer system down): claim holds; the outage is named on the record.",
         "Judgment-required edit unresolved: claim holds at the exception; the human's resolution re-enters through a fresh scrub."]),

 dict(num="P02", slug="prior-auth-cycle", name="Prior Authorization Cycle",
  desc="Swarm deployment: auth-required service to human-attested submission and tracked outcome. Agents 06, 03, 05, 04, 12, 13. Medical necessity is clinical - packages carry provider documentation, never swarm-authored argument.",
  trigger="`auth.request` at 06 from intake or scrubbing.",
  pre=["The payer rule table confirms the requirement (or the discrepancy tuple routed it here as required)."],
  phases=[
   ("Phase 1 - Package", [
    ("1","03","Coverage facts for auth routing","`eligibility.result` → 06, 13","payer and plan facts attached"),
    ("2","05","Clinical documentation per the auth checklist (sealed)","`doc.received` → 06, 13","custody references attached, content sealed"),
    ("3","06","Assemble the package: demographics, provider-entered codes, sealed docs","`auth.package` → human, 13","package delivered for clinical attestation - the human signs and submits"),
   ]),
   ("Phase 2 - Track", [
    ("4","06","Chase status per cadence; report outcome facts","`auth.status` → 02, 12, 13","auth number, valid dates, unit limits on record"),
    ("5","06","Patient status notices on approved templates","`patient.message.request` → 04","sends logged"),
    ("6","12","Validity window and expiry clocks armed","(clock instantiation)","expiry alerts at lead-time"),
   ]),
  ],
  gates=["No submission without the human's clinical attestation - the package waits, the swarm never signs.",
         "Peer-to-peer requests route to the human immediately; the swarm never voices medical necessity."],
  completion="Auth outcome facts on record with validity clocks armed; the gated service's claim path unblocked or the denial routed.",
  abort=["Auth denied: facts to 02 and human; appeal consideration follows the denial path with a human decision.",
         "Pended past the service-date lead-time: escalation with the pend reason verbatim; the human decides the service-day call."]),

 dict(num="P03", slug="claim-submission-cycle", name="Claim Submission Cycle",
  desc="Swarm deployment: gate-green package to payer-acknowledged submission. Agents 07, 02, 12, 13. Submitted means both artifacts - clearinghouse accept AND payer accept; the send log proves nothing.",
  trigger="`scrub.result` at 07.",
  pre=["Package carries its edit-table version and green gates; timely-filing clock is live via 12."],
  phases=[
   ("Phase 1 - Submit and confirm", [
    ("1","07","Submit; capture the clearinghouse acceptance artifact","`claim.submit` → external","clearinghouse accept on record"),
    ("2","07","Confirm payer acceptance; chase at lead-time if silent","`claim.status` → 10, 13","payer accept artifact on record - only now is it submitted"),
   ]),
   ("Phase 2 - Rejections", [
    ("3","07","Route rejections with codes verbatim; no local fixes","`rejection.notice` → 02, 13","rejection re-enters through a fresh scrub"),
   ]),
  ],
  gates=["No resubmission without a new scrub version - the duplicate-billing line.",
         "Timely-filing-critical claims escalate on any gate conflict; the clock never overrides a gate."],
  completion="Payer acceptance artifact on record; status tracking handed to A/R follow-up.",
  abort=["Payer acknowledgment absent past lead-time: claim is NOT submitted; escalation with the chase history."]),

 dict(num="P04", slug="payment-posting-reconciliation", name="Payment Posting & Reconciliation",
  desc="Swarm deployment: remittance to posted, reconciled, variance-visible financial records. Agents 08, 11, 12, 09, 13. Payer facts post verbatim; contract rules cite themselves; everything else needs signed authority.",
  trigger="ERA/EOB remittance arrives at 08.",
  pre=["Payer contract rules loaded are the owner-ratified versions; remit reference dedupe check passes."],
  phases=[
   ("Phase 1 - Post", [
    ("1","08","Post payments, contractual adjustments (rule cited per line), patient responsibility","`remit.posted` → 11, 13","every line tied to claim + remit reference"),
    ("2","08","Record variances against contract computation","`adjustment.record` → 12, 13","variance facts visible, never absorbed"),
    ("3","08","Route denials at posting time, codes verbatim","`denial.intake` → 09","no denial sits in a posted pile"),
   ]),
   ("Phase 2 - Patient-side effects", [
    ("4","11","Update patient balances; statement cycle picks up per policy","`billing.record` → 13","balance records current"),
   ]),
  ],
  gates=["Write-offs and non-contractual adjustments move only on signed `writeoff.authority` - unsigned is an integrity violation.",
         "A remit posted differently than the payer stated it, to balance, is the named failure."],
  completion="Remit fully posted with citations; variances recorded; denials in the denial pipeline; patient balances current.",
  abort=["Unruled adjustment code: payment posts, adjustment holds unapplied, human flagged.",
         "Authority anomaly (changed balance since signing): hold + re-confirm naming both states."]),

 dict(num="P05", slug="denial-appeal-cycle", name="Denial & Appeal Cycle",
  desc="Swarm deployment: posted denial to human-decided appeal with a complete package inside the deadline. Agents 09, 05, 12, 10, 13. The appeal decision, clinical argument, and signature are human - the swarm builds the package and watches the clock.",
  trigger="`denial.intake` at 09.",
  pre=["Denial codes and remarks captured verbatim at posting; appeal clock instantiated from the payer rule."],
  phases=[
   ("Phase 1 - Triage", [
    ("1","09","Triage per the ratified taxonomy; shorter-clock category wins ties","`denial.triage` → 10, 13","category + appeal deadline on record"),
    ("2","12","Appeal clock armed with lead-time alerts","`deadline.alert` → 09 (at lead-times)","clock live"),
   ]),
   ("Phase 2 - Package", [
    ("3","05","Appeal documentation per checklist (sealed custody)","`doc.received` → 09, 13","custody references attached"),
    ("4","09","Assemble the package: denial verbatim, claim history, sealed docs","`appeal.package` → human, 13","package delivered inside the lead-time for human decision + signature"),
   ]),
  ],
  gates=["No appeal is decided, authored (clinically), signed, or submitted by the swarm - human end to end.",
         "A denial never dies quietly: appeal decision or signed write-off authority, one or the other, on record."],
  completion="Appeal package delivered inside the lead-time; the human decision and outcome recorded.",
  abort=["Deadline certain to be missed: escalation with the miss quantified before it lands; the miss is named in the books."]),

 dict(num="P06", slug="ar-aging-followup", name="A/R Aging Follow-up",
  desc="Swarm deployment: aging accounts worked on cadence with facts, not pressure. Agents 10, 04, 12, 13. Payer chases produce status facts; patient contact runs the published sequence to its end - which is a human decision, never an invented next step.",
  trigger="Aging threshold or `deadline.alert` surfaces an account at 10.",
  pre=["The published patient-contact sequence and payer chase cadence are the ratified versions."],
  phases=[
   ("Phase 1 - Payer side", [
    ("1","10","Chase payer status per cadence; record facts with rep references","`payer.status` → 09, 12, 13","stated dates recorded as stated-by-payer, never as posted"),
   ]),
   ("Phase 2 - Patient side", [
    ("2","10","Run the published contact sequence via approved templates","`patient.message.request` → 04","sequence position recorded per contact; ceiling absolute"),
    ("3","04","Route replies by content; hardship verbatim to human","`patient.reply` → 10, 11","hardship statements never absorbed into the sequence"),
   ]),
  ],
  gates=["No settlement, negotiation, or collection referral originates in the swarm - human decisions with the full history attached.",
         "Contact beyond the published sequence is a conduct violation, not persistence."],
  completion="Accounts current-cycle worked: payer facts recorded, sequence positions advanced per rule, end-of-sequence accounts in the human queue with full history.",
  abort=["Sequence exhausted unresolved: human queue with the complete contact history - the sequence ends in a decision."]),

 dict(num="P07", slug="patient-billing-cycle", name="Patient Billing Cycle",
  desc="Swarm deployment: posted patient responsibility to statements, published-policy plans, and clean balance records. Agents 11, 04, 10, 13. Policy self-serves with its citation; everything beyond moves on signed authority.",
  trigger="`remit.posted` lands patient-responsibility amounts at 11, or the statement cycle date arrives.",
  pre=["Statement content merges only from the current posted record (11's stale-statement tuple)."],
  phases=[
   ("Phase 1 - Statements", [
    ("1","11","Generate statement records per the published cycle","`billing.record` → 13","statement record with posted-balance reference"),
    ("2","04","Statement sends on approved templates","`patient.message.send`","sends logged verbatim"),
   ]),
   ("Phase 2 - Plans", [
    ("3","11","Set up in-policy payment plans with the policy cited; exceptions route to human","`billing.record` → 13","plan terms + citation (or authority envelope_id) on record"),
    ("4","10","Missed-plan-payment handling per the published sequence","`patient.message.request` → 04","sequence facts recorded; no improvised consequences"),
   ]),
  ],
  gates=["Plan exceptions, discounts, and hardship arrangements execute only on signed `plan.authority`.",
         "Patient credits route to the human refund process - never auto-issued."],
  completion="Statements and plans current against the posted record; exceptions in the human queue with citations.",
  abort=["Balance changes mid-cycle: queued statements regenerate against the current record before send."]),

 dict(num="P08", slug="timely-filing-protection", name="Timely Filing Protection",
  desc="Swarm deployment: the filing-clock engine end to end - every claim's window tracked, at-risk claims surfaced at lead-time, certain misses escalated before they land. Agents 12, 07, 10, 14, 13. Clocks are facts; conservatism is ratified.",
  trigger="Continuous: clock instantiation on every claim path; alerts at ratified lead-times.",
  pre=["The payer rule table (filing limits per payer/plan) is the owner-ratified current version."],
  phases=[
   ("Continuous - the clock engine", [
    ("1","12","Instantiate filing clocks per payer on every claim; disputed dates run from the earlier","(clock set)","every claim carries its window"),
    ("2","12","Fire alerts at lead-times to the owners of the next action","`deadline.alert` → 07, 09, 10, 14","alerts logged with lead-time basis"),
    ("3","07","At-risk claims surface for priority handling; gate conflicts escalate","(priority handling)","no clock ever overrides a gate"),
    ("4","14","Clock reconciliation into the books: satisfied, at-risk, missed - misses quantified","(book sections)","misses named with owners, never buried"),
   ]),
  ],
  gates=["A certain miss is escalated the moment it is certain - early-reported certainty is compliance, late discovery is failure.",
         "Clocks are never rescheduled to fit workload."],
  completion="Continuous playbook: every active claim carries a live window; the books carry the reconciliation.",
  abort=["Rule-table gap for a payer: the clock runs on the most conservative known limit and the gap escalates for ratification."]),

 dict(num="P09", slug="morning-operations", name="Morning Operations",
  desc="Swarm deployment: the billing desk's morning book. Overnight remits and denials, today's filing and appeal clocks, auth expirations, aging exceptions - assembled from records for human review. Agents 14, 13, 12.",
  trigger="Scheduled daily start (owner-configured time) or owner command.",
  pre=["EOD books from the previous day exist (P10 completion on the log); if absent, the book runs with the gap NAMED."],
  phases=[
   ("Assemble (parallel, all to human review)", [
    ("1","14","Pull overnight remit/denial activity and aging exceptions","`record.request` → 13","overnight + exceptions sections sourced"),
    ("2","14","Today's clock alerts: filing, appeals, auth expirations","(from 12's alert stream)","clock section current with lead-times"),
   ]),
   ("Present", [
    ("3","14","Deliver the morning book; unavailable sources marked absent","`report.package` → human","book delivered; the human directs"),
   ]),
  ],
  gates=["A source unavailable at assembly is a named absence - never yesterday's numbers backfilled."],
  completion="Morning book delivered with every section sourced or marked absent.",
  abort=["Record source down: section marked absent; the book still delivers on time."]),

 dict(num="P10", slug="end-of-day-books", name="End-of-Day Books",
  desc="Swarm deployment: the closing books. Claims out, remits posted, denials triaged, appeals packaged, clock reconciliation, the missed-item sweep. Agents 14, 13, 12. Gaps named; a clean-looking book with hidden gaps is the named failure.",
  trigger="Scheduled day end (owner-configured time) or owner command.",
  pre=["The morning book (P09) exists as the sweep baseline; if absent, the sweep names that first."],
  phases=[
   ("Assemble", [
    ("1","14","Pull the day's activity chronology: submissions, postings, denials, appeals, plans","`record.request` → 13","activity sections sourced with timestamps"),
    ("2","14","Clock reconciliation: satisfied, at-risk, missed - misses quantified with owners","(from 12's stream + records)","reconciliation complete"),
    ("3","14","Missed-item sweep against the morning book","(sweep vs. P09 baseline)","sweep complete; no silent reassignment"),
   ]),
   ("Present", [
    ("4","14","Deliver the EOD books","`report.package` → human","books delivered; P10 completion event logged for tomorrow's P09"),
   ]),
  ],
  gates=["The sweep never reassigns - it names. Reassignment is the human's morning decision."],
  completion="EOD books delivered; sweep complete with owners named; completion event logged.",
  abort=["Morning baseline absent: the sweep names that first and proceeds on records alone."]),
]
def main():
    os.makedirs(ROOT, exist_ok=True)
    for p in PB:
        d = os.path.join(ROOT, f"{p['num']}-{p['slug']}")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "SKILL.md"), "w").write(build(p))
        print("emitted", p["num"])

if __name__ == "__main__":
    main()
