"""Core boot test: this identity, loaded into the vendored dispatcher core.

Added 2026-10-12 when the core (dispatcher-agents) was synced into this
repo. It proves the identity plugs into the core as shipped:

  - the loader accepts the identity (routes.json, priority.json, one
    SKILL.md per numbered agent dir);
  - every route leaving to `external` carries a declared, verified audience
    class, so none falls through to the fail-closed default by omission;
  - a message to the principal (the party this identity serves) is
    delivered at once;
  - a message to a counterparty is held at the disclosure gate, is not
    delivered, and goes out once on a signed disclosure.authority - an
    unsigned release, or a second release of the same message, sends nothing;
  - every `.authority` lane refuses an unsigned envelope;
  - a sender not on a route is rejected, and an intent on no route is
    held for the broker; neither is delivered.

Nothing here names an intent: every case is read from identity/routes.json,
so the same file runs in every identity repo.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pytest  # noqa: E402

from dispatcher.core import AUDIENCE, AUDIENCE_GATED, AuditLog, Envelope, Routes  # noqa: E402
from dispatcher.hub import Hub  # noqa: E402
from dispatcher.loader import load_identity  # noqa: E402
from dispatcher.signatures import Ed25519Signer  # noqa: E402

ROUTES_PATH = os.path.join(ROOT, "identity", "routes.json")
ROUTES = json.load(open(ROUTES_PATH))["routes"]
EXTERNAL = [r for r in ROUTES if "external" in r["receivers"]]
AUTHORITY = [r for r in ROUTES
             if r["intent"].endswith(".authority") and r["senders"] == ["human"]]


def _prov(src):
    return {"source": src, "captured_at": "runtime", "verbatim_available": True}


def _hub(tmp_path):
    signer = Ed25519Signer()
    hub = Hub(Routes(ROUTES_PATH),
              AuditLog(os.path.join(str(tmp_path), "audit.jsonl")),
              signature_verifier=signer.verifier())
    delivered = []
    hub.register("external", delivered.append)
    for r in ROUTES:
        for a in r["senders"] + r["receivers"]:
            if a.isdigit() and a not in hub.handlers:
                hub.register(a, lambda env: None)
    hub.register("human", lambda env: None)
    hub.on_turn_start()
    return hub, signer, delivered


def _outbound(route, ctx="boot-1"):
    return Envelope(from_agent=route["senders"][0], to_agent="external",
                    intent=route["intent"], client_context_id=ctx,
                    payload={"body": "boot test"},
                    provenance=_prov(f"spoke-{route['senders'][0]}"))


def _release(signer, held, sign=True):
    auth = Envelope(from_agent="human", to_agent=held.from_agent,
                    intent="disclosure.authority",
                    client_context_id=held.client_context_id,
                    payload={"held_envelope_id": held.envelope_id},
                    provenance=_prov("human"))
    if sign:
        signer.sign(auth)
    return auth


def _clean(hub):
    assert hub.queues.get("dead.letter", []) == [], hub.queues["dead.letter"]
    assert hub.audit.verify_chain()["ok"]


def test_loader_accepts_identity():
    ident = load_identity(ROOT)
    assert ident.n_routes == len(ROUTES)
    assert ident.priority_classes, "priority.json carries no classes"
    numbered = sorted(d[:2] for d in os.listdir(ROOT)
                      if d[:2].isdigit() and d[2:3] == "-"
                      and os.path.isdir(os.path.join(ROOT, d)))
    assert sorted(ident.agents) == numbered


def test_every_external_route_declares_a_verified_audience():
    assert EXTERNAL, "identity has no outbound route - nothing to gate"
    for r in EXTERNAL:
        assert r.get("audience") in AUDIENCE, r
        assert r.get("audience_verified") is True, r


@pytest.mark.parametrize("route", [r for r in EXTERNAL
                                   if r.get("audience") not in AUDIENCE_GATED],
                         ids=lambda r: r["intent"])
def test_principal_message_is_delivered(tmp_path, route):
    hub, signer, delivered = _hub(tmp_path)
    env = _outbound(route)
    res = hub.send(env)
    assert res["status"] == "ack", res
    assert [e.envelope_id for e in delivered] == [env.envelope_id]
    _clean(hub)


@pytest.mark.parametrize("route", [r for r in EXTERNAL
                                   if r.get("audience") in AUDIENCE_GATED],
                         ids=lambda r: r["intent"])
def test_counterparty_message_holds_until_signed_release(tmp_path, route):
    hub, signer, delivered = _hub(tmp_path)
    env = _outbound(route)
    res = hub.send(env)
    assert res["status"] == "held" and res["reason"] == "absolute_signal", res
    assert delivered == []
    # an unsigned release sends nothing and leaves the hold in place
    bad = hub.release_disclosure(_release(signer, env, sign=False))
    assert bad["status"] == "reject", bad
    assert delivered == [] and env.envelope_id in hub._absolute_holds
    # the signed release sends the original, once
    ok = hub.release_disclosure(_release(signer, env))
    assert ok["status"] == "ack", ok
    assert [e.envelope_id for e in delivered] == [env.envelope_id]
    # a second release of the same message sends nothing more
    again = hub.release_disclosure(_release(signer, env))
    assert again["status"] == "reject", again
    assert len(delivered) == 1
    _clean(hub)


@pytest.mark.parametrize("route", AUTHORITY or [None],
                         ids=lambda r: r["intent"] if r else "none")
def test_authority_lane_refuses_unsigned(tmp_path, route):
    if route is None:
        pytest.skip("identity declares no human .authority lane")
    hub, signer, _ = _hub(tmp_path)
    got = []
    target = route["receivers"][0]
    hub.register(target, got.append)
    env = Envelope(from_agent="human", to_agent=target, intent=route["intent"],
                   client_context_id="boot-auth", payload={"amount": 1},
                   provenance=_prov("human"))
    res = hub.send(env)
    assert res["status"] != "ack", res
    assert got == []
    # the same envelope, signed, is delivered
    signed = Envelope(from_agent="human", to_agent=target,
                      intent=route["intent"], client_context_id="boot-auth",
                      payload={"amount": 1}, provenance=_prov("human"))
    signer.sign(signed)
    assert hub.send(signed)["status"] == "ack"
    assert [e.envelope_id for e in got] == [signed.envelope_id]


def test_closed_track_rejects_a_sender_not_on_the_route(tmp_path):
    hub, signer, delivered = _hub(tmp_path)
    route = EXTERNAL[0]
    agents = sorted({a for r in ROUTES for a in r["senders"] if a.isdigit()})
    stranger = next(a for a in agents if a not in route["senders"])
    env = Envelope(from_agent=stranger, to_agent="external",
                   intent=route["intent"], client_context_id="boot-x",
                   payload={}, provenance=_prov(f"spoke-{stranger}"))
    res = hub.send(env)
    assert res["status"] == "reject" and "tuple illegal" in res["reason"], res
    assert delivered == []


def test_intent_off_the_track_is_held_not_delivered(tmp_path):
    hub, signer, delivered = _hub(tmp_path)
    env = Envelope(from_agent=EXTERNAL[0]["senders"][0], to_agent="external",
                   intent="not.on.the.track", client_context_id="boot-y",
                   payload={}, provenance=_prov("spoke"))
    res = hub.send(env)
    assert res["status"] == "held" and res["queue"] == "clarification.request", res
    assert delivered == []
