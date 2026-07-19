#!/usr/bin/env python3
"""Watch the medical-billing swarm work - a real run, not a slideshow.

One patient, start to finish, against the real hub with the real closed
track, real Ed25519 signatures, and the real hash-chained audit log:

  Act 1  Encounter -> gate-green claim (eligibility + edits, codes verbatim)
  Act 2  Submission with BOTH acceptance artifacts
  Act 3  Remit posts: contract adjustment cited, one-cent variance caught,
         denial triaged two-lane, credit balance surfaces + 60-day clock
  Act 4  Unsigned refund REJECTED by the hub; signed refund executes
  Act 5  Patient says STOP: sequence dies same turn, one confirmation
  Act 6  Chain verification - every event above, hash-linked, tamper-evident

Run it:  python3 tools/run_demo.py
"""
import os
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dispatcher.core import Envelope, Routes, AuditLog
from dispatcher.hub import Hub
from dispatcher.signatures import Ed25519Signer, Ed25519Verifier
from dispatcher.medbilling_spokes import (
    Spoke01EncounterIntake, Spoke02ClaimScrubbing, Spoke03Eligibility,
    Spoke04PatientComm, Spoke05DocCollection, Spoke06PriorAuth,
    Spoke07Submission, Spoke08PaymentPosting, Spoke09DenialMgmt,
    Spoke10ARFollowup, Spoke11PatientBilling, Spoke12ComplianceDeadlines,
    Spoke13Records, Spoke14DailyOps)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def say(s=""):
    print(s)


def act(n, title):
    say(); say(f"{'='*66}"); say(f"  ACT {n}: {title}"); say('='*66)


def main():
    tmp = tempfile.mkdtemp()
    signer = Ed25519Signer()
    verifier = Ed25519Verifier(signer.public_key_bytes())
    audit_path = os.path.join(tmp, "audit.jsonl")
    hub = Hub(Routes(os.path.join(ROOT, "identity", "routes.json")),
              AuditLog(audit_path), signature_verifier=verifier.verifier())
    external = []
    hub.register("external", lambda e: external.append(e))
    hub.register("human", lambda e: None)
    s = {"01": Spoke01EncounterIntake(hub, provider_roster={"dr-a"},
                                      auth_required_codes=set()),
         "02": Spoke02ClaimScrubbing(hub, edit_tables={"version": "e1",
                                                       "rules": []}),
         "03": Spoke03Eligibility(hub),
         "04": Spoke04PatientComm(hub, templates={
             "statement": "Your balance is {balance}.",
             "opt_out_confirmed": "We will stop billing reminders."}),
         "05": Spoke05DocCollection(hub),
         "06": Spoke06PriorAuth(hub),
         "07": Spoke07Submission(hub),
         "08": Spoke08PaymentPosting(hub, contract_rules={
             "CO45": {"rule_id": "PAYER1-CO45"}}),
         "09": Spoke09DenialMgmt(hub, taxonomy={"CO50": "medical_necessity"}),
         "10": Spoke10ARFollowup(hub),
         "11": Spoke11PatientBilling(hub, contact_sequence=[
             {"day": 0, "step": "statement", "template": "statement"}]),
         "12": Spoke12ComplianceDeadlines(hub),
         "13": Spoke13Records(hub),
         "14": Spoke14DailyOps(hub)}
    for aid, sp in s.items():
        if aid != "01":
            hub.register(aid, sp.handle)
    hub.on_turn_start()
    ctx = "demo-patient-1"

    act(1, "ENCOUNTER -> GATE-GREEN CLAIM")
    s["03"].db[ctx] = {"status": "active"}
    s["01"].capture(ctx, {"patient": "p1", "provider": "dr-a",
                          "dos": "2026-07-01", "codes": ["99213"],
                          "units": 1, "pos": "11",
                          "field_provenance": {k: "ehr" for k in
                                               ("patient", "provider", "dos",
                                                "units", "pos")}})
    st = s["02"].claims[ctx]
    say(f"  eligibility: active (payer-timestamped)")
    say(f"  edit tables: {st['edit_version']} run, 0 judgment exits")
    say(f"  codes on the released claim: {st['codes']}  <- provider-entered,"
        " untouched")
    say(f"  RELEASED: {st['released']}")

    act(2, "SUBMISSION - BOTH ARTIFACTS OR IT DIDN'T HAPPEN")
    say(f"  claim.submit went to external: "
        f"{any(e.intent=='claim.submit' for e in external)}")
    say("  clearinghouse ack arrives... (payer ack still missing ->"
        " NOT submitted)")
    s["07"].clearinghouse_ack(ctx)
    confirmed = [e for e in hub.audit.read()
                 if e["kind"] == "envelope.persisted"
                 and e["intent"] == "claim.status"]
    say(f"  confirmed submissions so far: {len(confirmed)}")
    s["07"].payer_ack(ctx)
    confirmed = [e for e in hub.audit.read()
                 if e["kind"] == "envelope.persisted"
                 and e["intent"] == "claim.status"]
    say(f"  payer ack arrives -> confirmed submissions: {len(confirmed)}"
        "  (artifacts: ch_ack + payer_ack)")

    act(3, "REMIT POSTS - THE $0.00 RULE, TWO-LANE TRIAGE, THE 60-DAY CLOCK")
    s["08"].post_remit(ctx, {
        "remit_ref": "remit-771", "paid": 79.99, "expected_paid": 80.00,
        "adjustments": [{"code": "CO45", "amount": 20.0},
                        {"code": "CO99", "amount": 3.0}],
        "denied_lines": [{"code": "CO50"}],
        "credit_balance": 12.50})
    events = [e for e in hub.audit.read() if e["kind"] == "envelope.persisted"]
    def count(i): return len([e for e in events if e["intent"] == i])
    say(f"  contract adjustment CO45: applied WITH citation"
        f" (adjustment.record x{count('adjustment.record')})")
    say(f"  unruled adjustment CO99: HELD unapplied"
        f" ({s['08'].ledger[ctx]['held_adjustments']})")
    say(f"  paid 79.99 vs expected 80.00 -> reconciliation.exception"
        f" x{count('reconciliation.exception')}  <- one cent, human notified")
    say(f"  denial CO50 (medical necessity) -> lane: human_packet"
        f" (denial.triage x{count('denial.triage')}) - the swarm never argues"
        " necessity")
    say(f"  credit balance $12.50 -> on the patient ledger"
        f" ({s['11'].accounts[ctx]['credit']}) and the 60-day federal clock"
        f" is ARMED ({[c['kind'] for c in s['12'].clocks[ctx]]})")

    act(4, "MONEY: UNSIGNED IS REJECTED, SIGNED EXECUTES")
    unsigned = Envelope(from_agent="human", to_agent="08",
                        intent="refund.authority", client_context_id=ctx,
                        payload={"amount": 12.50},
                        provenance={"source": "human",
                                    "captured_at": "runtime",
                                    "verbatim_available": True})
    res = hub.send(unsigned)
    say(f"  unsigned refund.authority -> hub says ok={res.get('ok', False)}"
        f"  refund executed: {s['08'].refunds.get(ctx)}")
    signed_env = Envelope(from_agent="human", to_agent="08",
                          intent="refund.authority", client_context_id=ctx,
                          payload={"amount": 12.50},
                          provenance={"source": "human",
                                      "captured_at": "runtime",
                                      "verbatim_available": True})
    signer.sign(signed_env)
    hub.send(signed_env)
    say(f"  SIGNED refund.authority (Ed25519) -> refund executed:"
        f" {s['08'].refunds.get(ctx)}")

    act(5, "THE PATIENT SAYS STOP")
    s["11"].statement_due(ctx, 0)
    say("  statement sent (published sequence, day 0)")
    s["04"].patient_reply(ctx, "STOP - no more messages please")
    say(f"  patient.optout fired -> 10, 11, 13; one confirmation sent,"
        " then silence")
    say(f"  next statement attempt: "
        f"{s['11'].statement_due(ctx, 30)!r}")

    act(6, "THE CHAIN - EVERY EVENT ABOVE, HASH-LINKED")
    result = hub.audit.verify_chain()
    n = len(hub.audit.read())
    say(f"  audit entries: {n}")
    say(f"  verify_chain(): ok={result['ok']}")
    say(f"  dead letters: {len(hub.queues['dead.letter'])}")
    say(f"  log file: {audit_path}")
    say()
    say("  Tamper with any line of that file and verify_chain() names the"
        " line.")
    say("  That's the whole pitch: not trust us - check us.")
    say()


if __name__ == "__main__":
    main()
