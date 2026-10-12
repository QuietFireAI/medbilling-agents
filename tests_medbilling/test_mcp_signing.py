"""MCP signing gate (ported 2026-10-12 from listing-assistants audit MCP-1).

The MCP server holds a key it generates at boot. It must sign nothing for a
host unless it was started with --demo-signing; otherwise an authority
action over MCP would prove only that the host asked. These tests drive the
GovernedIdentity behind the MCP surface directly (no MCP package needed).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dispatcher import identity_mcp as mcp  # noqa: E402

ROUTES = json.load(open(os.path.join(ROOT, "identity", "routes.json")))["routes"]
AUTH = next(r for r in ROUTES
            if r["intent"].endswith(".authority") and r["senders"] == ["human"])


def _identity(demo):
    routes, signer, verifier = mcp._boot_conformance()
    return mcp.GovernedIdentity(routes, signer, verifier, demo_signing=demo)


def _persisted(gi, intent):
    return [e for e in gi.hub.audit.read()
            if e["kind"] == "envelope.persisted" and e["intent"] == intent]


def _payload():
    return {"to": AUTH["receivers"][0], "amount": 1.0}


def test_server_does_not_sign_for_host_by_default():
    gi = _identity(demo=False)
    r = gi.authority(AUTH["intent"], _payload(), "DEMO_SIGN_WITH_SERVER_KEY")
    assert r["ok"] is False and "--demo-signing" in r["reason"], r
    assert _persisted(gi, AUTH["intent"]) == []
    assert gi.describe()["governance"]["server_signs_for_host"] is False


def test_unsigned_authority_rejected_by_hub():
    gi = _identity(demo=False)
    r = gi.authority(AUTH["intent"], _payload())
    assert r["ok"] is False and r["hub_status"] != "ack", r
    assert _persisted(gi, AUTH["intent"]) == []


def test_demo_signing_mode_signs_and_says_so():
    gi = _identity(demo=True)
    assert gi.describe()["governance"]["server_signs_for_host"] is True
    r = gi.authority(AUTH["intent"], _payload(), "DEMO_SIGN_WITH_SERVER_KEY")
    assert r["ok"] is True and r["hub_status"] == "ack", r
    assert len(_persisted(gi, AUTH["intent"])) == 1


def test_authority_needs_a_named_receiver():
    gi = _identity(demo=True)
    r = gi.authority(AUTH["intent"], {"amount": 1.0}, "DEMO_SIGN_WITH_SERVER_KEY")
    assert r["ok"] is False and "payload.to" in r["reason"], r
    assert _persisted(gi, AUTH["intent"]) == []


def test_only_this_identitys_spokes_are_wired():
    gi = _identity(demo=False)
    assert list(gi.KNOWN) == [gi.spoke_mod.__name__.split(".")[-1]]
    assert gi.describe()["runtime"] == "wired"
    r = gi.submit("listing.authorize", {})
    assert r["ok"] is False, r
