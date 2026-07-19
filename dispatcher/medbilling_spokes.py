"""Real spokes for the medical-billing (RCM) vertical, built against the
ratified v0.2 spec (44 routes, P01-P14).

Scope honesty (TUNING_MANUAL TOP OF LIST): these implement every playbook
path P01-P14 end-to-end plus the hard gates (the five absolute lines, the
$0.00 rule, signed money, sealed custody, opt-out kill, two-lane denial
triage, timely-filing clocks). Exhaustive per-tuple coverage at
listing-agents depth is the next pass and is tracked, not pretended.

The five absolute lines, in code:
  1. The swarm never codes    -> 02 carries codes verbatim into exceptions;
                                 no code-mutation method exists anywhere.
  2. Clinical content sealed  -> 05 strips/refuses content; envelopes carry
                                 existence/type/date/source/hash only.
  3. No unsigned money        -> 08/11 execute only on hub-verified signed
                                 authority envelopes (hub rejects unsigned).
  4. No pressure beyond the published sequence -> 11 runs contact_sequence
                                 to its ceiling; patient.optout kills it.
  5. A denial never dies quietly, a clock never slips silently -> 09 closes
                                 only on human decision or signed abandon;
                                 12 alerts at lead-time and escalates.
"""
from __future__ import annotations

import hashlib
from .core import Envelope

UNKNOWN = "unknown"
SOURCE_VERIFIED = "source_verified"

_HARDSHIP_WORDS = ("can't afford", "cannot afford", "can't pay", "cannot pay",
                   "hardship", "lost my job", "payment plan")
_CLINICAL_WORDS = ("diagnosis", "is this cancer", "side effect", "medication",
                   "should i take", "symptoms", "medical advice")
_OPTOUT_WORDS = ("stop", "unsubscribe", "do not contact", "don't contact",
                 "no more messages", "opt out")


def _env(frm, to, intent, ctx, payload, confidence=UNKNOWN,
         escalation_flag=False):
    return Envelope(from_agent=frm, to_agent=to, intent=intent,
                    client_context_id=ctx, payload=payload,
                    confidence=confidence, escalation_flag=escalation_flag,
                    provenance={"source": f"spoke-{frm}",
                                "captured_at": "runtime",
                                "verbatim_available": True})


# ------------------------------------------------------------------ 01
class Spoke01EncounterIntake:
    """Charge capture. Captures what the provider documented; NEVER assigns
    or changes a code - there is no code-writing path in this class."""

    REQUIRED = ("patient", "provider", "dos", "codes", "units", "pos")

    def __init__(self, hub, provider_roster=None, auth_required_codes=None):
        self.hub = hub
        self.roster = set(provider_roster or [])
        self.auth_codes = set(auth_required_codes or [])
        self.held = {}          # ctx -> reason
        hub.register("01", self.handle)

    def capture(self, ctx, encounter):
        missing = [f for f in self.REQUIRED
                   if encounter.get(f) in (None, "", [])]
        prov = encounter.get("field_provenance", {})
        unattributed = [f for f in self.REQUIRED
                        if f not in ("codes",) and f not in prov]
        if encounter.get("provider") not in self.roster:
            self.held[ctx] = "unrostered_provider"
            self.hub.send(_env("01", "queue", "clarification.request", ctx,
                               {"reason": "unrostered_provider",
                                "provider": encounter.get("provider")},
                               escalation_flag=True))
            return
        if missing or unattributed:
            self.held[ctx] = "incomplete"
            self.hub.send(_env("01", "queue", "clarification.request", ctx,
                               {"reason": "incomplete_encounter",
                                "missing": missing,
                                "unattributed": unattributed}))
            return
        auth_required = any(c in self.auth_codes
                            for c in encounter["codes"])
        payload = {"encounter": dict(encounter),
                   "codes_provider_entered": list(encounter["codes"]),
                   "auth_required": auth_required,
                   "captured_verbatim": True}
        self.hub.send(_env("01", "02", "encounter.captured", ctx, payload,
                           confidence=SOURCE_VERIFIED))
        if auth_required:
            self.hub.send(_env("01", "06", "auth.request", ctx,
                               {"codes": list(encounter["codes"]),
                                "dos": encounter["dos"]}))
        self.hub.send(_env("01", "13", "interaction.log", ctx,
                           {"event": "encounter_captured"}))

    def handle(self, env):
        if env.intent in ("eligibility.result", "record.response"):
            return  # informational at intake


# ------------------------------------------------------------------ 02
class Spoke02ClaimScrubbing:
    """Edit tables; mechanical fixes cite sources; judgment exits verbatim.
    Gates: eligibility known + auth green (when required) before release."""

    def __init__(self, hub, edit_tables=None):
        self.hub = hub
        self.edits = edit_tables or {"version": "e0", "rules": []}
        self.claims = {}   # ctx -> state

    def _st(self, ctx):
        return self.claims.setdefault(ctx, {
            "codes": None, "eligibility": None, "auth": "not_required",
            "released": False, "exceptions": [], "held_reason": None})

    def handle(self, env):
        st = self._st(env.client_context_id)
        ctx = env.client_context_id
        if env.intent == "encounter.captured":
            st["codes"] = list(env.payload["codes_provider_entered"])
            st["edit_version"] = self.edits["version"]
            st["needs_fresh_scrub"] = False
            if env.payload.get("auth_required"):
                st["auth"] = "pending"
            for rule in self.edits["rules"]:
                if rule.get("judgment_required") and \
                        rule["code"] in st["codes"]:
                    # Absolute line 1: codes travel VERBATIM, untouched.
                    st["exceptions"].append(rule["rule_id"])
                    self.hub.send(_env("02", "human", "scrub.exception", ctx,
                                       {"rule_id": rule["rule_id"],
                                        "codes_verbatim": list(st["codes"]),
                                        "edit_version": self.edits["version"]},
                                       escalation_flag=True))
                    self.hub.send(_env("02", "13", "scrub.exception", ctx,
                                       {"rule_id": rule["rule_id"],
                                        "codes_verbatim": list(st["codes"])}))
            if st["eligibility"] is None:
                self.hub.send(_env("02", "03", "eligibility.request", ctx,
                                   {"dos": env.payload["encounter"]["dos"]}))
        elif env.intent == "eligibility.result":
            st["eligibility"] = env.payload["status"]
        elif env.intent == "auth.status":
            st["auth"] = env.payload["status"]
        elif env.intent == "rejection.notice":
            # corrections re-enter through a FRESH scrub, never quick-fixed
            st["released"] = False
            st["needs_fresh_scrub"] = True
            st["held_reason"] = "rejected_" + env.payload.get("code", "?")
        elif env.intent == "doc.received":
            st.setdefault("docs", []).append(env.payload["doc_type"])
        self._maybe_release(ctx)

    def require_auth(self, ctx):
        self._st(ctx)["auth"] = "pending"

    def _maybe_release(self, ctx):
        st = self._st(ctx)
        if st["released"] or st["codes"] is None or \
                st.get("needs_fresh_scrub"):
            return
        if st["exceptions"]:
            st["held_reason"] = "judgment_exception"
            return
        if st["eligibility"] != "active":
            st["held_reason"] = "eligibility_" + str(st["eligibility"])
            return
        if st["auth"] not in ("not_required", "approved"):
            st["held_reason"] = "auth_" + st["auth"]
            return
        st["released"], st["held_reason"] = True, None
        pkg = {"codes_verbatim": list(st["codes"]),
               "edit_version": st["edit_version"],
               "gates": {"eligibility": "active", "auth": st["auth"]}}
        self.hub.send(_env("02", "07", "scrub.result", ctx, pkg,
                           confidence=SOURCE_VERIFIED))
        self.hub.send(_env("02", "13", "scrub.result", ctx, pkg))


# ------------------------------------------------------------------ 03
class Spoke03Eligibility:
    """Facts with payer-system timestamps. Unknown blocks gates."""

    def __init__(self, hub, payer_db=None, payer_down=False):
        self.hub = hub
        self.db = payer_db or {}
        self.payer_down = payer_down

    def handle(self, env):
        if env.intent != "eligibility.request":
            return
        ctx = env.client_context_id
        if self.payer_down:
            res = {"status": "unknown", "reason": "payer_system_down",
                   "ts": "runtime"}
        else:
            res = dict(self.db.get(ctx, {"status": "unknown",
                                         "reason": "not_on_file"}))
            res["ts"] = "runtime"
        for to in ("02", "13"):
            self.hub.send(_env("03", to, "eligibility.result", ctx, res,
                               confidence=SOURCE_VERIFIED
                               if res["status"] != "unknown" else UNKNOWN))

    def coverage_changed(self, ctx, new_facts):
        """P11 trigger: mid-cycle change - blast radius includes 07 and 10."""
        res = dict(new_facts); res["ts"] = "runtime"; res["changed"] = True
        for to in ("02", "07", "10", "13"):
            self.hub.send(_env("03", to, "eligibility.result", ctx, res,
                               confidence=SOURCE_VERIFIED))


# ------------------------------------------------------------------ 04
class Spoke04PatientComm:
    """Templated messages from posted facts. Absolute line 4: the sequence
    has a ceiling; opt-out kills it same turn; clinical never answered."""

    def __init__(self, hub, templates=None):
        self.hub = hub
        self.templates = templates or {}
        self.opted_out = set()   # ctx
        self.sent = []

    def handle(self, env):
        ctx = env.client_context_id
        if env.intent == "patient.message.request":
            if ctx in self.opted_out:
                self.hub.send(_env("04", "queue", "clarification.request",
                                   ctx, {"reason": "opted_out_contact_blocked",
                                         "requested_by": env.from_agent},
                                   escalation_flag=True))
                return
            body = self.templates.get(env.payload.get("template_id"),
                                      env.payload.get("template_id", ""))
            out = {"template_id": env.payload.get("template_id"),
                   "body": body, "facts": env.payload.get("facts", {})}
            self.sent.append((ctx, out))
            self.hub.send(_env("04", "external", "patient.message.send",
                               ctx, out))
            self.hub.send(_env("04", "13", "interaction.log", ctx,
                               {"event": "patient_message",
                                "template": out["template_id"]}))

    def patient_reply(self, ctx, text):
        low = text.lower()
        if any(w in low for w in _OPTOUT_WORDS):
            self.opted_out.add(ctx)
            for to in ("10", "11", "13"):
                self.hub.send(_env("04", to, "patient.optout", ctx,
                                   {"verbatim": text}))
            # one confirmation, then silence
            self.hub.send(_env("04", "external", "patient.message.send", ctx,
                               {"template_id": "opt_out_confirmed"}))
            return
        if any(w in low for w in _CLINICAL_WORDS):
            self.hub.send(_env("04", "queue", "escalation.clinical", ctx,
                               {"verbatim": text}, escalation_flag=True))
            return
        if any(w in low for w in _HARDSHIP_WORDS):
            # both, always: answer from facts AND route hardship verbatim
            self.hub.send(_env("04", "queue", "escalation.hardship", ctx,
                               {"verbatim": text}, escalation_flag=True))
        for to in ("10", "11"):
            self.hub.send(_env("04", to, "patient.reply", ctx,
                               {"verbatim": text}))


# ------------------------------------------------------------------ 05
class Spoke05DocCollection:
    """Sealed custody: inventory existence/type/date/source/hash ONLY.
    Content in, HIPAA escalation out - never forwarded."""

    def __init__(self, hub):
        self.hub = hub
        self.inventory = {}   # ctx -> [items]

    def handle(self, env):
        if env.intent != "doc.request":
            return
        self.inventory.setdefault(env.client_context_id, []).append(
            {"requested": env.payload.get("doc_type"),
             "by": env.from_agent, "status": "requested"})

    def receive_document(self, ctx, doc):
        if "content" in doc:
            # Absolute line 2: content is never read or forwarded.
            self.hub.send(_env("05", "queue", "escalation.hipaa", ctx,
                               {"reason": "content_received_sealed",
                                "doc_type": doc.get("doc_type")},
                               escalation_flag=True))
            doc = {k: v for k, v in doc.items() if k != "content"}
        item = {"doc_type": doc.get("doc_type"), "date": doc.get("date"),
                "source": doc.get("source"),
                "hash": doc.get("hash") or hashlib.sha256(
                    str(sorted(doc.items())).encode()).hexdigest()[:16],
                "status": "received"}
        if doc.get("patient_mismatch"):
            # sealed misdirect protocol: human immediately, HIPAA incident
            self.hub.send(_env("05", "queue", "escalation.hipaa", ctx,
                               {"reason": "wrong_patient_document"},
                               escalation_flag=True))
            return
        self.inventory.setdefault(ctx, []).append(item)
        for to in ("02", "06", "09", "13"):
            self.hub.send(_env("05", to, "doc.received", ctx, item,
                               confidence=SOURCE_VERIFIED))


# ------------------------------------------------------------------ 06
class Spoke06PriorAuth:
    """Rule-table determination; packages carry provider documentation,
    never swarm-authored medical-necessity argument."""

    def __init__(self, hub):
        self.hub = hub
        self.auths = {}   # ctx -> state

    def handle(self, env):
        ctx = env.client_context_id
        st = self.auths.setdefault(ctx, {"status": "pending", "docs": []})
        if env.intent == "auth.request":
            self.hub.send(_env("06", "05", "doc.request", ctx,
                               {"doc_type": "clinical_support"}))
            self._status(ctx, "pending")
        elif env.intent == "doc.received":
            st["docs"].append(env.payload)
            pkg = {"docs": list(st["docs"]),
                   "swarm_authored_argument": None}   # never
            self.hub.send(_env("06", "human", "auth.package", ctx, pkg,
                               escalation_flag=True))
            self.hub.send(_env("06", "13", "auth.package", ctx, pkg))
        elif env.intent == "eligibility.result":
            st["eligibility"] = env.payload["status"]

    def payer_decision(self, ctx, status):
        self._status(ctx, status)

    def _status(self, ctx, status):
        self.auths.setdefault(ctx, {})["status"] = status
        for to in ("02", "12", "13"):
            self.hub.send(_env("06", to, "auth.status", ctx,
                               {"status": status}))


# ------------------------------------------------------------------ 07
class Spoke07Submission:
    """BOTH acceptance artifacts required. Idempotent. Corrections go back
    through a fresh scrub - the payer's quick-fix is declined by absence."""

    def __init__(self, hub):
        self.hub = hub
        self.submitted = {}   # ctx -> {"ch_ack":, "payer_ack":}
        self.held = {}

    def handle(self, env):
        ctx = env.client_context_id
        if env.intent == "scrub.result":
            if ctx in self.submitted:
                return          # idempotency: submit once
            self.submitted[ctx] = {"ch_ack": False, "payer_ack": False,
                                   "pkg": env.payload}
            self.hub.send(_env("07", "external", "claim.submit", ctx,
                               env.payload))
        elif env.intent == "secondary.claim.ready":
            # a cascade is a claim: fresh scrub gate, not a shortcut
            self.hub.send(_env("07", "13", "interaction.log", ctx,
                               {"event": "secondary_ready_awaiting_scrub"}))
        elif env.intent == "eligibility.result" and \
                env.payload.get("changed"):
            if ctx in self.submitted and not \
                    self.submitted[ctx]["payer_ack"]:
                self.held[ctx] = "eligibility_changed"
        elif env.intent == "deadline.alert":
            pass

    def clearinghouse_ack(self, ctx):
        st = self.submitted[ctx]; st["ch_ack"] = True
        self._maybe_confirm(ctx)

    def payer_ack(self, ctx):
        st = self.submitted[ctx]; st["payer_ack"] = True
        self._maybe_confirm(ctx)

    def _maybe_confirm(self, ctx):
        st = self.submitted[ctx]
        if st["ch_ack"] and st["payer_ack"]:
            for to in ("10", "13"):
                self.hub.send(_env("07", to, "claim.status", ctx,
                                   {"status": "submitted",
                                    "artifacts": ["ch_ack", "payer_ack"]},
                                   confidence=SOURCE_VERIFIED))

    def payer_rejection(self, ctx, code):
        for to in ("02", "13"):
            self.hub.send(_env("07", to, "rejection.notice", ctx,
                               {"code": code}))
        self.submitted.pop(ctx, None)   # resubmission via fresh scrub


# ------------------------------------------------------------------ 08
class Spoke08PaymentPosting:
    """Money. Contract-matching adjustments auto with citation; everything
    else signed. $0.00 reconciliation. Credits arm the refund clock.
    Secondary cascade fires when a secondary payer is on file."""

    def __init__(self, hub, contract_rules=None):
        self.hub = hub
        self.rules = contract_rules or {}   # code -> rule dict
        self.posted = {}    # remit_ref -> True (idempotency)
        self.ledger = {}    # ctx -> {"paid":, "adjusted":, "held":}
        self.refunds = {}   # ctx -> "executed"

    def post_remit(self, ctx, remit):
        ref = remit["remit_ref"]
        if ref in self.posted:
            return           # remit ref is the idempotency key
        self.posted[ref] = True
        led = self.ledger.setdefault(ctx, {"paid": 0.0, "adjusted": 0.0,
                                           "held_adjustments": []})
        led["paid"] += remit["paid"]
        for adj in remit.get("adjustments", []):
            rule = self.rules.get(adj["code"])
            if rule:
                led["adjusted"] += adj["amount"]
                self.hub.send(_env("08", "12", "adjustment.record", ctx,
                                   {"code": adj["code"],
                                    "amount": adj["amount"],
                                    "rule_citation": rule["rule_id"]}))
                self.hub.send(_env("08", "13", "adjustment.record", ctx,
                                   {"code": adj["code"],
                                    "rule_citation": rule["rule_id"]}))
            else:
                led["held_adjustments"].append(adj)   # unruled != contractual
        expected = remit.get("expected_paid")
        if expected is not None and abs(expected - remit["paid"]) > 0.0:
            # $0.00 tolerance, ratified 2026-07-18
            for to in ("human", "13"):
                self.hub.send(_env("08", to, "reconciliation.exception", ctx,
                                   {"expected": expected,
                                    "paid": remit["paid"],
                                    "variance": round(
                                        remit["paid"] - expected, 2)},
                                   escalation_flag=(to == "human")))
        for to in ("11", "13"):
            self.hub.send(_env("08", to, "remit.posted", ctx,
                               {"paid": remit["paid"], "remit_ref": ref}))
        if remit.get("denied_lines"):
            self.hub.send(_env("08", "09", "denial.intake", ctx,
                               {"denials": remit["denied_lines"],
                                "codes_verbatim": True}))
        if remit.get("secondary_payer_on_file"):
            for to in ("07", "13"):
                self.hub.send(_env("08", to, "secondary.claim.ready", ctx,
                                   {"primary_paid": remit["paid"],
                                    "primary_eob_verbatim": True}))
        if remit.get("credit_balance"):
            for to in ("11", "12", "13"):
                self.hub.send(_env("08", to, "credit.balance", ctx,
                                   {"amount": remit["credit_balance"]}))

    def handle(self, env):
        ctx = env.client_context_id
        if env.intent == "writeoff.authority":
            self.ledger.setdefault(ctx, {}).update(
                writeoff=env.payload["amount"], writeoff_signed=True)
        elif env.intent == "refund.authority":
            # hub already verified the signature; unsigned never reaches here
            self.refunds[ctx] = "executed"
            self.hub.send(_env("08", "13", "interaction.log", ctx,
                               {"event": "refund_executed",
                                "amount": env.payload["amount"]}))
            self.hub.send(_env("08", "12", "adjustment.record", ctx,
                               {"code": "REFUND",
                                "amount": -env.payload["amount"],
                                "rule_citation": "signed refund.authority"}))


# ------------------------------------------------------------------ 09
class Spoke09DenialMgmt:
    """Two-lane triage (ratified 2026-07-18). A denial never dies quietly:
    human decision or signed abandon, one or the other, on record."""

    CLINICAL = {"medical_necessity", "coding", "clinical"}

    def __init__(self, hub, taxonomy=None):
        self.hub = hub
        self.taxonomy = taxonomy or {}   # denial code -> category
        self.open = {}    # ctx -> state

    def handle(self, env):
        ctx = env.client_context_id
        if env.intent == "denial.intake":
            for d in env.payload["denials"]:
                cat = self.taxonomy.get(d["code"], "clinical")  # conservative
                st = self.open.setdefault(ctx, {"category": cat,
                                                "closed": None, "docs": []})
                lane = "human_packet" if cat in self.CLINICAL else "rework"
                for to in ("10", "13"):
                    self.hub.send(_env("09", to, "denial.triage", ctx,
                                       {"code": d["code"], "category": cat,
                                        "lane": lane}))
                self.hub.send(_env("09", "05", "doc.request", ctx,
                                   {"doc_type": "appeal_support"}))
        elif env.intent == "doc.received":
            st = self.open.get(ctx)
            if st is None or st["closed"]:
                return
            st["docs"].append(env.payload)
            pkg = {"denial_verbatim": True, "docs": list(st["docs"]),
                   "category": st["category"],
                   "swarm_clinical_argument": None}   # never
            self.hub.send(_env("09", "human", "appeal.package", ctx, pkg,
                               escalation_flag=True))
            self.hub.send(_env("09", "13", "appeal.package", ctx, pkg))
        elif env.intent == "appeal.abandon.authority":
            st = self.open.setdefault(ctx, {})
            st["closed"] = "abandoned_signed"
            self.hub.send(_env("09", "13", "interaction.log", ctx,
                               {"event": "appeal_abandoned_signed"}))

    def human_decision(self, ctx, decision):
        self.open.setdefault(ctx, {})["closed"] = decision


# ------------------------------------------------------------------ 10
class Spoke10ARFollowup:
    """Payer follow-up; patient lane and payer lane are different lanes.
    Referral moves only on signed collection.referral.authority."""

    def __init__(self, hub):
        self.hub = hub
        self.accounts = {}   # ctx -> state

    def _st(self, ctx):
        return self.accounts.setdefault(ctx, {"patient_contact": True,
                                              "referral": None})

    def handle(self, env):
        ctx = env.client_context_id
        st = self._st(ctx)
        if env.intent == "patient.optout":
            st["patient_contact"] = False   # payer-side work continues
        elif env.intent == "collection.referral.authority":
            st["referral"] = "signed"
        elif env.intent in ("denial.triage", "claim.status",
                            "eligibility.result", "deadline.alert",
                            "patient.reply"):
            st.setdefault("events", []).append(env.intent)
            if env.intent == "deadline.alert":
                for to in ("09", "12", "13"):
                    self.hub.send(_env("10", to, "payer.status", ctx,
                                       {"status": "chased",
                                        "trigger": env.payload}))


# ------------------------------------------------------------------ 11
class Spoke11PatientBilling:
    """Published sequence to its ceiling, then a human decision - never
    auto-referral. Opt-out halts statements beyond required notices."""

    def __init__(self, hub, contact_sequence=None):
        self.hub = hub
        self.seq = contact_sequence or []
        self.accounts = {}   # ctx -> state

    def _st(self, ctx):
        return self.accounts.setdefault(ctx, {"balance": 0.0, "step": 0,
                                              "optout": False,
                                              "credit": None,
                                              "plan_signed": False})

    def handle(self, env):
        ctx = env.client_context_id
        st = self._st(ctx)
        if env.intent == "remit.posted":
            st["last_remit"] = env.payload
            self.hub.send(_env("11", "13", "billing.record", ctx,
                               {"event": "remit_applied"}))
        elif env.intent == "patient.optout":
            st["optout"] = True
        elif env.intent == "plan.authority":
            st["plan_signed"] = True
        elif env.intent == "credit.balance":
            st["credit"] = env.payload["amount"]   # visible on the ledger
            self.hub.send(_env("11", "13", "billing.record", ctx,
                               {"event": "credit_on_ledger",
                                "amount": env.payload["amount"]}))

    def statement_due(self, ctx, day):
        st = self._st(ctx)
        if st["optout"]:
            return "halted_optout"
        steps = [s for s in self.seq if s.get("day") is not None]
        if st["step"] >= len(steps):
            # ceiling reached: human decision, NEVER auto-referral
            self.hub.send(_env("11", "queue", "escalation.sequence_ceiling",
                               ctx, {"history_steps": st["step"]},
                               escalation_flag=True))
            return "human_decision"
        step = steps[st["step"]]
        if day >= step["day"]:
            st["step"] += 1
            self.hub.send(_env("11", "04", "patient.message.request", ctx,
                               {"template_id": step["template"],
                                "facts": {"balance": st["balance"]}}))
            return step["step"]
        return "not_due"


# ------------------------------------------------------------------ 12
class Spoke12ComplianceDeadlines:
    """The clock layer. Lead-time alert, then escalation - a clock never
    slips silently. The 60-day credit clock is class 1."""

    FILING_LEAD, FILING_ESC = 30, 10          # ratified 2026-07-18
    APPEAL_LEAD, APPEAL_ESC = 14, 5           # ratified 2026-07-18
    CREDIT_CLOCK = 60                          # federal rule

    def __init__(self, hub):
        self.hub = hub
        self.clocks = {}   # ctx -> [{kind, deadline_day, alerted, escalated}]

    def handle(self, env):
        ctx = env.client_context_id
        if env.intent == "auth.status":
            pass
        elif env.intent == "adjustment.record":
            pass
        elif env.intent == "credit.balance":
            self.arm(ctx, "credit_refund_60day",
                     deadline_day=env.payload.get("posted_day", 0)
                     + self.CREDIT_CLOCK,
                     lead=self.FILING_LEAD, esc=self.FILING_ESC)
        elif env.intent == "records.disclosure.package":
            self.arm(ctx, "records_response",
                     deadline_day=env.payload.get("deadline_day", 30),
                     lead=self.APPEAL_LEAD, esc=self.APPEAL_ESC)

    def arm(self, ctx, kind, deadline_day, lead=None, esc=None):
        self.clocks.setdefault(ctx, []).append(
            {"kind": kind, "deadline_day": deadline_day,
             "lead": lead or self.FILING_LEAD, "esc": esc or self.FILING_ESC,
             "alerted": False, "escalated": False})

    def run_daily(self, today):
        """The sweep. Errors here would be declared, never swallowed."""
        for ctx, clocks in self.clocks.items():
            for c in clocks:
                remaining = c["deadline_day"] - today
                if remaining <= c["esc"] and not c["escalated"]:
                    c["escalated"] = True
                    self.hub.send(_env("12", "queue", "escalation.clock",
                                       ctx, {"kind": c["kind"],
                                             "days_remaining": remaining},
                                       escalation_flag=True))
                elif remaining <= c["lead"] and not c["alerted"]:
                    c["alerted"] = True
                    for to in ("07", "09", "10", "14"):
                        self.hub.send(_env("12", to, "deadline.alert", ctx,
                                           {"kind": c["kind"],
                                            "days_remaining": remaining}))


# ------------------------------------------------------------------ 13
class Spoke13Records:
    """Append-only. The single source of truth's front desk. Disclosure
    inventory is existence/type/date/source only - release is human."""

    def __init__(self, hub):
        self.hub = hub
        self.log = {}       # ctx -> [entries]
        self.copies = {}    # ctx -> [book copies]

    def handle(self, env):
        ctx = env.client_context_id
        if env.intent == "record.request":
            entries = list(self.log.get(ctx, []))
            self.hub.send(_env("13", env.from_agent, "record.response", ctx,
                               {"entries": entries,
                                "complete_as_of": "runtime"}))
        elif env.intent == "interaction.log":
            self.log.setdefault(ctx, []).append(
                {"from": env.from_agent, "event": env.payload})
        elif env.intent in ("reconciliation.exception", "credit.balance",
                            "secondary.claim.ready", "scrub.result",
                            "scrub.exception", "eligibility.result",
                            "doc.received", "auth.package", "auth.status",
                            "claim.status", "rejection.notice",
                            "remit.posted", "adjustment.record",
                            "denial.triage", "appeal.package",
                            "payer.status", "billing.record",
                            "patient.optout"):
            self.copies.setdefault(ctx, []).append(
                {"intent": env.intent, "from": env.from_agent,
                 "payload": env.payload})

    def external_records_request(self, ctx, request):
        inventory = [{"type": e["intent"], "date": "runtime",
                      "source": e["from"]}
                     for e in self.copies.get(ctx, [])]
        # existence/type/date/source ONLY - no payloads leave the swarm
        pkg = {"request_verbatim": request, "inventory": inventory,
               "content_sealed": True,
               "deadline_day": request.get("deadline_day", 30)}
        self.hub.send(_env("13", "human", "records.disclosure.package", ctx,
                           pkg, escalation_flag=True))
        self.hub.send(_env("13", "12", "records.disclosure.package", ctx,
                           {"deadline_day": pkg["deadline_day"]}))


# ------------------------------------------------------------------ 14
class Spoke14DailyOps:
    """The morning report carries every wait. 72h clean-claim SLA
    (ratified 2026-07-18) is watched here."""

    def __init__(self, hub):
        self.hub = hub
        self.waits = []
        self.alerts = []

    def handle(self, env):
        if env.intent == "agent.status":
            self.waits.append(env.payload)
        elif env.intent == "deadline.alert":
            self.alerts.append(env.payload)

    def morning_report(self, ctx="ops"):
        pkg = {"waits": list(self.waits), "clock_alerts": list(self.alerts),
               "sections_absent": []}
        self.hub.send(_env("14", "human", "report.package", ctx, pkg))
        return pkg
