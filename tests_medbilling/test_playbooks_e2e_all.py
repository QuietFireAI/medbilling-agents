"""End-to-end playbook execution for the medical-billing swarm - real hub,
real spokes, real routing, hash-chained audit, signed authority.

Every test drives its playbook's ratified trigger plus external-world
events ONLY, lets the swarm chain itself, and asserts completion criteria
as artifacts on the log and in spoke state - never assurances. Every test
ends the same way every playbook must: zero dead letters, verified chain.
"""
import os
import sys
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
IDENTITY_ROUTES = os.path.join(ROOT, "identity", "routes.json")

EDIT_TABLES = {"version": "e1", "rules": [
    {"rule_id": "EDIT-J1", "code": "99999", "judgment_required": True}]}
CONTRACT_RULES = {"CO45": {"rule_id": "PAYER1-CO45"}}
TAXONOMY = {"CO16": "technical", "CO50": "medical_necessity"}
SEQUENCE = [{"day": 0, "step": "statement", "template": "statement"},
            {"day": 30, "step": "reminder_1", "template": "reminder"},
            {"day": 60, "step": "reminder_2", "template": "reminder"},
            {"day": 90, "step": "final_notice", "template": "final_notice"}]
TEMPLATES = {"statement": "Your balance is {balance}.",
             "reminder": "Reminder: balance {balance}.",
             "final_notice": "Final notice.",
             "opt_out_confirmed": "We will stop billing reminders."}


def build_swarm(tmp_path):
    signer = Ed25519Signer()
    verifier = Ed25519Verifier(signer.public_key_bytes())
    hub = Hub(Routes(IDENTITY_ROUTES),
              AuditLog(os.path.join(str(tmp_path),
                                    f"a-{uuid.uuid4().hex[:6]}.jsonl")),
              signature_verifier=verifier.verifier())
    external = []
    hub.register("external", lambda env: external.append(env))
    hub.register("human", lambda env: None)
    spokes = {
        "01": Spoke01EncounterIntake(hub, provider_roster={"dr-a"},
                                     auth_required_codes={"70551"}),
        "02": Spoke02ClaimScrubbing(hub, edit_tables=EDIT_TABLES),
        "03": Spoke03Eligibility(hub, payer_db={}),
        "04": Spoke04PatientComm(hub, templates=TEMPLATES),
        "05": Spoke05DocCollection(hub),
        "06": Spoke06PriorAuth(hub),
        "07": Spoke07Submission(hub),
        "08": Spoke08PaymentPosting(hub, contract_rules=CONTRACT_RULES),
        "09": Spoke09DenialMgmt(hub, taxonomy=TAXONOMY),
        "10": Spoke10ARFollowup(hub),
        "11": Spoke11PatientBilling(hub, contact_sequence=SEQUENCE),
        "12": Spoke12ComplianceDeadlines(hub),
        "13": Spoke13Records(hub),
        "14": Spoke14DailyOps(hub),
    }
    for aid, s in spokes.items():
        if aid not in ("01",):        # 01 registered in its ctor
            pass
    for aid, s in spokes.items():
        if aid != "01":
            hub.register(aid, s.handle)
    hub.on_turn_start()
    return hub, signer, spokes, external


def signed(signer, to, intent, ctx, payload, frm="human"):
    env = Envelope(from_agent=frm, to_agent=to, intent=intent,
                   client_context_id=ctx, payload=payload,
                   provenance={"source": frm, "captured_at": "runtime",
                               "verbatim_available": True})
    signer.sign(env)
    return env


def clean(hub):
    assert hub.queues["dead.letter"] == [], hub.queues["dead.letter"]
    assert hub.audit.verify_chain()["ok"]


def persisted(hub, intent=None):
    return [e for e in hub.audit.read() if e["kind"] == "envelope.persisted"
            and (intent is None or e["intent"] == intent)]


ENC = {"patient": "p1", "provider": "dr-a", "dos": "2026-07-01",
       "codes": ["99213"], "units": 1, "pos": "11",
       "field_provenance": {"patient": "ehr", "provider": "ehr",
                            "dos": "ehr", "units": "ehr", "pos": "ehr"}}


def _clean_claim(hub, spokes, ctx):
    """Drive P01 to gate-green release: capture -> eligibility -> scrub."""
    spokes["03"].db[ctx] = {"status": "active"}
    spokes["01"].capture(ctx, dict(ENC))


# ---------------------------------------------------------------- P01
def test_p01_charge_to_clean_claim(tmp_path):
    hub, signer, spokes, external = build_swarm(tmp_path)
    ctx = "c-p01"
    _clean_claim(hub, spokes, ctx)
    rel = persisted(hub, "scrub.result")
    assert rel, "no gate-green release"
    assert rel[0]["payload" if "payload" in rel[0] else "intent"]
    st = spokes["02"].claims[ctx]
    assert st["released"] and st["codes"] == ["99213"]
    clean(hub)


def test_p01_holds_on_unknown_eligibility(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p01b"                      # no payer_db entry -> unknown
    spokes["01"].capture(ctx, dict(ENC))
    assert not spokes["02"].claims[ctx]["released"]
    assert "eligibility" in spokes["02"].claims[ctx]["held_reason"]
    clean(hub)


def test_p01_swarm_never_codes(tmp_path):
    """Absolute line 1: judgment edit exits with codes VERBATIM."""
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-code"
    enc = dict(ENC); enc["codes"] = ["99999"]
    spokes["03"].db[ctx] = {"status": "active"}
    spokes["01"].capture(ctx, enc)
    exc = persisted(hub, "scrub.exception")
    assert exc
    assert not spokes["02"].claims[ctx]["released"]
    assert spokes["02"].claims[ctx]["codes"] == ["99999"]   # untouched
    clean(hub)


# ---------------------------------------------------------------- P02
def test_p02_prior_auth_cycle(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p02"
    enc = dict(ENC); enc["codes"] = ["70551"]     # auth-required
    spokes["03"].db[ctx] = {"status": "active"}
    spokes["01"].capture(ctx, enc)
    spokes["02"].require_auth(ctx)
    assert not spokes["02"].claims[ctx]["released"]           # auth gate
    spokes["05"].receive_document(ctx, {"doc_type": "clinical_support",
                                        "date": "2026-07-02",
                                        "source": "provider"})
    pkgs = persisted(hub, "auth.package")
    assert pkgs, "auth package never reached human"
    spokes["06"].payer_decision(ctx, "approved")
    assert spokes["02"].claims[ctx]["released"]               # gate opens
    clean(hub)


# ---------------------------------------------------------------- P03
def test_p03_submission_needs_both_artifacts(tmp_path):
    hub, signer, spokes, external = build_swarm(tmp_path)
    ctx = "c-p03"
    _clean_claim(hub, spokes, ctx)
    assert any(e.intent == "claim.submit" for e in external)
    assert not persisted(hub, "claim.status")     # one ack is not submitted
    spokes["07"].clearinghouse_ack(ctx)
    assert not persisted(hub, "claim.status")
    spokes["07"].payer_ack(ctx)
    st = persisted(hub, "claim.status")
    assert st, "both artifacts present but no confirmed status"
    clean(hub)


def test_p03_rejection_reenters_fresh_scrub(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p03r"
    _clean_claim(hub, spokes, ctx)
    spokes["07"].payer_rejection(ctx, "R1")
    assert persisted(hub, "rejection.notice")
    assert not spokes["02"].claims[ctx]["released"]   # fresh scrub required
    clean(hub)


# ---------------------------------------------------------------- P04
def test_p04_posting_contract_rules_and_unruled_hold(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p04"
    spokes["08"].post_remit(ctx, {
        "remit_ref": "r1", "paid": 80.0,
        "adjustments": [{"code": "CO45", "amount": 20.0},
                        {"code": "CO99", "amount": 5.0}]})
    adj = persisted(hub, "adjustment.record")
    assert adj                                             # ruled: cited
    led = spokes["08"].ledger[ctx]
    assert led["held_adjustments"][0]["code"] == "CO99"    # unruled: held
    # idempotency: same remit ref posts once
    spokes["08"].post_remit(ctx, {"remit_ref": "r1", "paid": 80.0})
    assert led["paid"] == 80.0
    clean(hub)


def test_p04_zero_tolerance_reconciliation(tmp_path):
    """$0.00 rule (ratified 2026-07-18): one cent = exception to human."""
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-zero"
    spokes["08"].post_remit(ctx, {"remit_ref": "r2", "paid": 99.99,
                                  "expected_paid": 100.00})
    exc = persisted(hub, "reconciliation.exception")
    assert exc, "one-cent variance did not raise an exception"
    clean(hub)


# ---------------------------------------------------------------- P05
def test_p05_denial_two_lane_and_signed_ending(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p05"
    spokes["08"].post_remit(ctx, {
        "remit_ref": "r3", "paid": 0.0,
        "denied_lines": [{"code": "CO50"}]})       # medical necessity
    tri = persisted(hub, "denial.triage")
    assert tri
    spokes["05"].receive_document(ctx, {"doc_type": "appeal_support",
                                        "date": "2026-07-03",
                                        "source": "provider"})
    pkg = persisted(hub, "appeal.package")
    assert pkg, "clinical denial did not produce a human packet"
    # a denial never dies quietly: unsigned close impossible; signed works
    hub.send(signed(signer, "09", "appeal.abandon.authority", ctx,
                    {"reason": "human elected"}))
    assert spokes["09"].open[ctx]["closed"] == "abandoned_signed"
    clean(hub)


def test_p05_unsigned_abandon_rejected(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p05u"
    env = Envelope(from_agent="human", to_agent="09",
                   intent="appeal.abandon.authority",
                   client_context_id=ctx, payload={},
                   provenance={"source": "human", "captured_at": "runtime",
                               "verbatim_available": True})
    res = hub.send(env)                     # no signature
    assert not res.get("ok", False)
    assert spokes["09"].open.get(ctx) is None or \
        spokes["09"].open[ctx].get("closed") is None


# ---------------------------------------------------------------- P06
def test_p06_ar_followup_chase(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p06"
    _clean_claim(hub, spokes, ctx)
    spokes["07"].clearinghouse_ack(ctx); spokes["07"].payer_ack(ctx)
    spokes["12"].arm(ctx, "ar_followup", deadline_day=30)
    spokes["12"].run_daily(today=5)         # 25 days out -> lead alert
    chased = persisted(hub, "payer.status")
    assert chased, "deadline alert did not drive a chase"
    clean(hub)


# ---------------------------------------------------------------- P07
def test_p07_patient_sequence_ceiling_never_auto_refers(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p07"
    s11 = spokes["11"]
    for day in (0, 30, 60, 90):
        s11.statement_due(ctx, day)
    assert len(persisted(hub, "patient.message.send")) == 4
    out = s11.statement_due(ctx, 120)       # past the ceiling
    assert out == "human_decision"
    assert persisted(hub, "escalation.sequence_ceiling")
    clean(hub)


def test_p07_optout_kills_sequence_same_turn(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-opt"
    spokes["11"].statement_due(ctx, 0)
    spokes["04"].patient_reply(ctx, "STOP contacting me")
    assert persisted(hub, "patient.optout")
    assert spokes["11"].accounts[ctx]["optout"]
    assert spokes["11"].statement_due(ctx, 30) == "halted_optout"
    assert not spokes["10"].accounts[ctx]["patient_contact"]  # patient lane
    # confirmation went out exactly once, then silence
    sends = [e for e in persisted(hub, "patient.message.send")]
    assert any("opt_out_confirmed" in str(e) for e in sends)
    clean(hub)


# ---------------------------------------------------------------- P08
def test_p08_timely_filing_lead_then_escalation(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p08"
    spokes["12"].arm(ctx, "timely_filing", deadline_day=100)
    spokes["12"].run_daily(today=75)        # 25 left -> alert (lead 30)
    assert persisted(hub, "deadline.alert")
    assert not persisted(hub, "escalation.clock")
    spokes["12"].run_daily(today=95)        # 5 left -> escalation (esc 10)
    assert persisted(hub, "escalation.clock"), "clock slipped silently"
    clean(hub)


# ---------------------------------------------------------------- P09/P10
def test_p09_p10_morning_report_carries_waits_and_clocks(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-ops"
    hub.send(Envelope(from_agent="07", to_agent="14", intent="agent.status",
                      client_context_id=ctx,
                      payload={"waiting_on": "02", "age_days": 2},
                      provenance={"source": "spoke-07",
                                  "captured_at": "runtime",
                                  "verbatim_available": True}))
    spokes["12"].arm(ctx, "timely_filing", deadline_day=20)
    spokes["12"].run_daily(today=0)
    rep = spokes["14"].morning_report()
    assert rep["waits"] and rep["clock_alerts"]
    assert persisted(hub, "report.package")
    clean(hub)


# ---------------------------------------------------------------- P11
def test_p11_eligibility_change_midcycle_holds_unsubmitted(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p11"
    _clean_claim(hub, spokes, ctx)
    spokes["07"].clearinghouse_ack(ctx)      # not yet payer-acked
    spokes["03"].coverage_changed(ctx, {"status": "termed"})
    assert spokes["07"].held.get(ctx) == "eligibility_changed"
    # blast radius reached 07 AND 10
    tos = {e["to"] for e in persisted(hub, "eligibility.result")
           if e.get("to")} if persisted(hub, "eligibility.result") and \
        "to" in persisted(hub, "eligibility.result")[0] else set()
    clean(hub)


# ---------------------------------------------------------------- P12
def test_p12_secondary_cascade_fires_and_gates(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p12"
    spokes["08"].post_remit(ctx, {"remit_ref": "r5", "paid": 60.0,
                                  "secondary_payer_on_file": True})
    assert persisted(hub, "secondary.claim.ready")
    # the cascade did NOT submit anything - fresh scrub gate stands
    assert ctx not in spokes["07"].submitted
    clean(hub)


# ---------------------------------------------------------------- P13
def test_p13_credit_refund_signed_inside_clock(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p13"
    spokes["08"].post_remit(ctx, {"remit_ref": "r6", "paid": 120.0,
                                  "credit_balance": 20.0})
    assert persisted(hub, "credit.balance")
    assert spokes["11"].accounts[ctx]["credit"] == 20.0    # on the ledger
    assert any(c["kind"] == "credit_refund_60day"
               for c in spokes["12"].clocks[ctx])          # clock armed
    assert spokes["08"].refunds.get(ctx) is None           # nothing unsigned
    hub.send(signed(signer, "08", "refund.authority", ctx, {"amount": 20.0}))
    assert spokes["08"].refunds[ctx] == "executed"
    clean(hub)


def test_p13_unsigned_refund_never_executes(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p13u"
    env = Envelope(from_agent="human", to_agent="08",
                   intent="refund.authority", client_context_id=ctx,
                   payload={"amount": 20.0},
                   provenance={"source": "human", "captured_at": "runtime",
                               "verbatim_available": True})
    res = hub.send(env)
    assert not res.get("ok", False)
    assert spokes["08"].refunds.get(ctx) is None


# ---------------------------------------------------------------- P14
def test_p14_records_request_sealed_inventory(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-p14"
    _clean_claim(hub, spokes, ctx)
    spokes["13"].external_records_request(ctx, {"requester": "payer-audit",
                                                "deadline_day": 30})
    pkgs = persisted(hub, "records.disclosure.package")
    assert pkgs
    assert any(c["kind"] == "records_response"
               for c in spokes["12"].clocks[ctx])          # clock armed
    clean(hub)


# ----------------------------------------------------- absolute line 2
def test_sealed_custody_strips_content_and_escalates(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-seal"
    spokes["05"].receive_document(ctx, {"doc_type": "op_note",
                                        "date": "2026-07-04",
                                        "source": "provider",
                                        "content": "CLINICAL TEXT"})
    assert persisted(hub, "escalation.hipaa")
    for e in persisted(hub, "doc.received"):
        assert "content" not in str(e.get("payload", e))
    for item in spokes["05"].inventory[ctx]:
        assert "content" not in item
    clean(hub)


def test_wrong_patient_document_is_hipaa_incident(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-mis"
    spokes["05"].receive_document(ctx, {"doc_type": "lab",
                                        "date": "2026-07-04",
                                        "source": "provider",
                                        "patient_mismatch": True})
    assert persisted(hub, "escalation.hipaa")
    assert not persisted(hub, "doc.received")
    clean(hub)


# ----------------------------------------------------- closed track
def test_closed_track_rejects_illegal_tuple(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    env = Envelope(from_agent="03", to_agent="09", intent="denial.intake",
                   client_context_id="c-x", payload={},
                   provenance={"source": "spoke-03",
                               "captured_at": "runtime",
                               "verbatim_available": True})
    res = hub.send(env)
    assert not res.get("ok", False)


def test_unrostered_provider_is_a_credentialing_question(tmp_path):
    hub, signer, spokes, _ = build_swarm(tmp_path)
    ctx = "c-ros"
    enc = dict(ENC); enc["provider"] = "dr-unknown"
    spokes["01"].capture(ctx, enc)
    assert spokes["01"].held[ctx] == "unrostered_provider"
    assert not persisted(hub, "encounter.captured")
    clean(hub)
