#!/usr/bin/env python3
"""gen_diagrams.py - the pictures in this identity's docs, generated so they
cannot drift from the spec they draw.

The same file ships in every identity repo (freight, medbilling, claim, hr,
enrollment, practice, mortgage, property-mgmt); it finds this repo's
data by its *_data.py and *_playbooks.py modules.

What it draws:
  NN-*/README.md            each agent: who it hears from, who it talks to
                            (identity/routes.json; words from the agent's own
                            edge table in the data module)
  playbooks/PNN-*/README.md each playbook's ratified steps, phase by phase,
                            with its trigger, your hard stops and its done-line
  playbooks/README.md       all playbooks by priority class (identity/priority.json)
  docs/PLAY-BY-PLAY.md      (medbilling, claim) a numbered picture of a real
                            run of the playbook's end-to-end test
  pictures placed on README, ROSTER, DEPLOY, INSTALL, INTEGRATIONS,
  AFTER_ACTION, docs/TUNING_MANUAL and, where present, docs/START_HERE,
  docs/MOUNTING, docs/SERVING_HERMES_OPENCLAW, docs/OPERATOR_TESTING_MANUAL,
  docs/PLAYBOOKS, docs/WHAT_SUCCESS_MEANS, docs/JOB_DESCRIPTIONS.

Usage:
    python tools/gen_diagrams.py           # write
    python tools/gen_diagrams.py --check   # exit 1 if any file differs
Run it after the other generators (generate_skills, gen_meta, gen_playbooks,
gen_docs): they rewrite some of these files whole.
"""
from __future__ import annotations

import argparse
import glob
import importlib
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

def _one(pattern):
    found = sorted(glob.glob(os.path.join(ROOT, pattern)))
    assert len(found) == 1, f"expected one {pattern} in {ROOT}, found {found}"
    return os.path.basename(found[0])[:-3]


KIND = _one("*_data.py")[:-len("_data")]          # freight, medbilling, ...
DATA = importlib.import_module(f"{KIND}_data")
PB = [dict(p) for p in importlib.import_module(f"{KIND}_playbooks").PB]
# claim keeps P01-P10's completion line and abort paths in gen_playbooks.CA
# instead of the data module; read them from there when the data lacks them.
_CA = getattr(importlib.import_module("gen_playbooks"), "CA", {})
for _p in PB:
    if "completion" not in _p and _p["num"] in _CA:
        _p["completion"], _p["abort"] = _CA[_p["num"]]
TESTS = "tests_property_mgmt" if KIND == "property" else f"tests_{KIND}"

# Who "you" are in each vertical.
HUMAN = {
    "freight": "You (the broker)",
    "medbilling": "You (billing staff)",
    "claim": "You (the adjuster)",
    "hr": "You (HR)",
    "enrollment": "You (admissions)",
    "practice": "You (the front office)",
    "mortgage": "You (the loan officer)",
    "property": "You (the property manager)",
}[KIND]

# Real end-to-end test runs drawn in docs/PLAY-BY-PLAY.md. Only tests that
# run the playbook they are numbered for are listed. Tests are looked up in
# every test_playbooks_*.py module of the repo's test folder.
RUNS = {
    "medbilling": {
        "P01": "test_p01_charge_to_clean_claim",
        "P02": "test_p02_prior_auth_cycle",
        "P03": "test_p03_submission_needs_both_artifacts",
        "P04": "test_p04_posting_contract_rules_and_unruled_hold",
        "P05": "test_p05_denial_two_lane_and_signed_ending",
        "P06": "test_p06_ar_followup_chase",
        "P07": "test_p07_patient_sequence_ceiling_never_auto_refers",
        "P08": "test_p08_timely_filing_lead_then_escalation",
        "P09": "test_p09_p10_morning_report_carries_waits_and_clocks",
        "P10": "test_p09_p10_morning_report_carries_waits_and_clocks",
        "P11": "test_p11_eligibility_change_midcycle_holds_unsubmitted",
        "P12": "test_p12_secondary_cascade_fires_and_gates",
        "P13": "test_p13_credit_refund_signed_inside_clock",
        "P14": "test_p14_records_request_sealed_inventory",
    },
    "claim": {
        "P01": "test_p01_fnol_to_dispatch",
        "P02": "test_p02_property_claim_lifecycle",
        "P03": "test_p03_auto_claim_lifecycle",
        "P04": "test_p04_total_loss_settlement_records",
        "P05": "test_p05_fraud_silent_aggregation_signed_ending",
        "P06": "test_p06_subro_preparation_human_money",
        "P07": "test_p07_signed_payment_and_zero_tolerance",
        "P08": "test_p08_doi_inquiry_clock_and_human_package",
        "P09": "test_p09_p10_morning_report",
        "P10": "test_p09_p10_morning_report",
        "P11": "test_p11_representation_halt_all_three_detectors",
        "P12": "test_p12_policy_change_midclaim",
        "P13": "test_p13_salvage_recovery_cascade",
        "P14": "test_p14_records_request_privilege_flagged",
    },
}.get(KIND, {})

ROUTINE = {"interaction.log", "agent.status"}
AMBIENT = {
    "clarification.request": "asks you",
    "integrity.violation": "reports an integrity problem",
    "interaction.log": "logs it to the record",
    "agent.status": "reports what it is waiting on",
    "config.update": "your signed settings",
    "disclosure.authority": "you sign the release",
}
OUTSIDE = "Outside world"

YOU = "classDef you fill:#f2cc60,stroke:#9a6700,color:#1f2328"
STOP = "classDef stop fill:#ffd8d3,stroke:#cf222e,color:#1f2328"
OK = "classDef ok fill:#dafbe1,stroke:#1a7f37,color:#1f2328"
ME = "classDef me fill:#1f6feb,stroke:#1f6feb,color:#ffffff"
OUTC = "classDef out fill:#d0d7de,stroke:#57606a,color:#1f2328"


def clean(text, n=80):
    t = re.sub(r"\s+", " ", str(text)).strip().replace("`", "")
    t = t.replace(";", ",").replace("#", "no.").replace('"', "'")
    t = t.replace("<", "(").replace(">", ")").replace(":", " -").replace("&", "and")
    t = t.replace("{", "(").replace("}", ")").replace("|", "/")
    return t if len(t) <= n else t[: n - 3].rstrip() + "..."


# ------------------------------------------------------------ the spec
ROUTES = json.load(open(os.path.join(ROOT, "identity", "routes.json")))["routes"]
AGENTS = {a["num"]: a for a in DATA.AGENTS}


def short(name):
    return re.sub(r" Agent$", "", name)


def label(aid):
    if aid in ("human", "queue"):
        return HUMAN
    if aid == "external":
        return OUTSIDE
    if aid == "00":
        return "00 Dispatcher"
    return f"{aid} {short(AGENTS[aid]['name'])}"


def _edges(aid, direction):
    for d, _route, trigger, intents in AGENTS.get(aid, {}).get("edges", []):
        if d == direction:
            yield trigger, set(re.findall(r"`([a-z_.*]+)`", intents))


FALLBACKS: set[str] = set()


def phrase(intent, frm, to):
    """The edge's words from the sender's table, else the receiver's, else
    a fixed phrase for swarm-wide duties, else the intent's own words."""
    for trig, ints in _edges(frm, "OUT"):
        if intent in ints:
            return trig
    for trig, ints in _edges(to, "IN"):
        if intent in ints:
            return trig
    if intent == "escalation.*":
        return "flags it for you"
    if intent.startswith("escalation."):
        return "flags it for you (" + intent.split(".", 1)[1].replace("_", " ") + ")"
    if intent in AMBIENT:
        return AMBIENT[intent]
    FALLBACKS.add(intent)
    return intent.replace(".", " ").replace("_", " ")


# ------------------------------------------------------------ agents
HUB_FLOW = f"""```mermaid
flowchart TD
    M["A message arrives at the hub"] --> D{{"Seen this exact<br/>message before?"}}
    D -- yes --> DUP["Not delivered twice"]
    D -- no --> L{{"Same topic going<br/>round in a loop?"}}
    L -- yes --> SUS["Paused - you are asked"]
    L -- no --> S{{"Properly formed?"}}
    S -- no --> R1["Refused"]
    S -- yes --> A{{"Needs your signature?"}}
    A -- "yes, and it is missing or wrong" --> R2["Refused and reported to you"]
    A -- "no, or signed" --> T{{"On the closed track?"}}
    T -- "wrong sender or receiver" --> R3["Refused"]
    T -- "a kind of message no lane knows" --> H1["Held - you are asked"]
    T -- yes --> O{{"Leaving the swarm for someone<br/>other than the party you serve?"}}
    O -- yes --> H2["Held until you sign the release"]
    O -- no --> P["Written to the tamper-evident log"]
    H2 -. "you sign" .-> P
    P --> C{{"Final self-check<br/>(when installed) passes?"}}
    C -- no --> H3["Held - you are asked"]
    C -- yes --> DL{{"Delivered?"}}
    DL -- no --> DEAD["Recorded as undeliverable;<br/>a crashed agent is flagged to you"]
    DL -- yes --> ACK["Only now: confirmed done"]
    {YOU}
    {STOP}
    {OK}
    class SUS,H1,H2,H3 you
    class R1,R2,R3,DUP,DEAD stop
    class ACK ok
```"""


def agent_diagram(aid):
    ins, outs = {}, {}

    def add(table, who, words):
        table.setdefault(who, [])
        if words not in table[who]:
            table[who].append(words)

    for r in ROUTES:
        intent, snd, rcv = r["intent"], r["senders"], r["receivers"]
        if intent == "config.update":
            add(ins, "human", phrase(intent, "human", aid))
            continue
        if aid in snd or "any" in snd:
            for to in rcv:
                if to != aid:
                    add(outs, to, phrase(intent, aid, to))
        if aid in rcv or "any" in rcv:
            agents_in = [s for s in snd if s.isdigit()]
            if "any" in snd or len(agents_in) >= 8:
                add(ins, "many", phrase(intent, "any", aid))
                for s in snd:
                    if not s.isdigit() and s != "any":
                        add(ins, s, phrase(intent, s, aid))
            else:
                for s in snd:
                    if s != aid:
                        add(ins, s, phrase(intent, s, aid))
    me = f"A{aid}"

    def node(who, side):
        if who in ("human", "queue"):
            return f"{side}B", f'{side}B(["{clean(HUMAN)}"])', "you"
        if who == "external":
            return f"{side}X", f'{side}X[/"{OUTSIDE}"/]', "out"
        if who == "many":
            return f"{side}M", f'{side}M["Most of the other agents"]', None
        return f"{side}{who}", f'{side}{who}["{clean(label(who))}"]', None

    lines = ["```mermaid", "flowchart LR"]
    styled = {"you": [], "out": []}
    for title, table, side in (("Hears from", ins, "I"), ("Talks to", outs, "O")):
        if not table:
            continue
        lines += [f'    subgraph {side}G["{title}"]', "        direction TB"]
        for who in table:
            nid, decl, cls = node(who, side)
            lines.append(f"        {decl}")
            if cls:
                styled[cls].append(nid)
        lines.append("    end")
        if side == "I":
            lines.append(f'    {me}(("{clean(label(aid))}"))')
    if not ins:
        lines.append(f'    {me}(("{clean(label(aid))}"))')
    for who, ps in ins.items():
        lines.append(f'    {node(who, "I")[0]} -- "{"<br/>".join(clean(p, 75) for p in ps)}" --> {me}')
    for who, ps in outs.items():
        lines.append(f'    {me} -- "{"<br/>".join(clean(p, 75) for p in ps)}" --> {node(who, "O")[0]}')
    lines += [f"    {ME}", f"    {YOU}", f"    {OUTC}", f"    class {me} me"]
    for cls, ids in styled.items():
        if ids:
            lines.append(f"    class {','.join(ids)} {cls}")
    lines.append("```")
    return "\n".join(lines)


def agent_dirs():
    return {os.path.basename(d)[:2]: d for d in sorted(glob.glob(os.path.join(ROOT, "[0-1][0-9]-*")))}


def agent_readme(aid, folder, playbooks_for):
    a = AGENTS.get(aid)
    title = "Dispatcher" if aid == "00" else short(a["name"])
    lead = (a["role"].split("\n\n")[0].replace("\n", " ") if a else
            "The hub: it validates every message against the closed track, "
            "holds what it cannot route, and owns the audit log.")
    parts = [f"# Agent {aid} - {title}", "", lead, ""]
    if aid == "00":
        parts += ["## What it does with every message", "",
                  "Every message between agents, to you, or to the outside world "
                  "passes through the hub. These are its checks, in the order "
                  "`dispatcher/hub.py` runs them. Yellow: waits for you. Red: "
                  "stopped. Green: done.", "", HUB_FLOW, ""]
    else:
        parts += ["## Who it works with", "",
                  "Left: who sends this agent messages. Right: who it sends "
                  "messages to. The blue circle is the agent; the yellow box is "
                  "you. Every arrow is a lane on the closed track "
                  "(`identity/routes.json`); the hub refuses any message that is "
                  "not on one.", "", agent_diagram(aid), ""]
        pbs = playbooks_for.get(aid, [])
        parts += ["## Playbooks it works in", ""]
        parts += [f"- [{num} {name}](../playbooks/{num}-{slug}/README.md)" for num, name, slug in pbs] \
            or ["- (none list it as a step)"]
        parts.append("")
    parts += ["## The rules it follows", "",
              "- [SKILL.md](SKILL.md) - its job, its limits, and when it stops and asks you",
              "- [DECISIONS.md](DECISIONS.md) - the decisions made ahead of time for it", "",
              "*Generated by `tools/gen_diagrams.py`; edit the data or the generator, "
              "not this file.*", ""]
    return "\n".join(parts)


# ------------------------------------------------------------ playbooks
def playbook_diagram(p):
    lines = ["```mermaid", "flowchart TB",
             f'    T(["Starts when - {clean(p["trigger"], 90)}"])']
    prev = "T"
    for i, (title, rows) in enumerate(p["phases"], 1):
        g = f"PH{i}"
        lines.append(f'    subgraph {g}["{clean(title, 60)}"]')
        parallel = "parallel" in title.lower()
        lines.append(f"        direction {'LR' if parallel else 'TB'}")
        ids = []
        for row in rows:
            step, aid, action = row[0], row[1], row[2]
            sid = f"S{i}_{re.sub(r'[^0-9A-Za-z]', '', step) or len(ids)}"
            who = clean(label(aid), 40) if aid in AGENTS or aid == "00" else clean(aid, 20)
            lines.append(f'        {sid}["{clean(step, 6)}. {who}<br/>{clean(action, 70)}"]')
            ids.append(sid)
        if not parallel:
            for a, b in zip(ids, ids[1:]):
                lines.append(f"        {a} --> {b}")
        lines.append("    end")
        lines.append(f"    {prev} --> {g}")
        prev = g
    lines.append(f'    DONE(["Done when - {clean(p["completion"], 110)}"])')
    lines.append(f"    {prev} --> DONE")
    if p.get("gates"):
        g = p["gates"][:4]
        more = f"<br/>+{len(p['gates']) - 4} more in SKILL.md" if len(p["gates"]) > 4 else ""
        body = "<br/>".join("- " + clean(x, 120) for x in g)
        lines.append(f'    GATE["Hard stops - {clean(HUMAN, 40)} decide<br/>{body}{more}"]')
        lines.append('    PH1 -. "at any step" .-> GATE')
    if p.get("abort"):
        a = p["abort"][:3]
        more = f"<br/>+{len(p['abort']) - 3} more in SKILL.md" if len(p["abort"]) > 3 else ""
        body = "<br/>".join("- " + clean(x, 120) for x in a)
        lines.append(f'    ABORT["Stops instead if<br/>{body}{more}"]')
        lines.append('    T -. "if" .-> ABORT')
    lines += [f"    {YOU}", f"    {STOP}", f"    {OK}", "    class DONE ok"]
    if p.get("gates"):
        lines.append("    class GATE you")
    if p.get("abort"):
        lines.append("    class ABORT stop")
    lines.append("```")
    return "\n".join(lines)


def playbook_readme(p):
    cls = PRIORITY["classes"].get(p["num"])
    return "\n".join([
        f"# Playbook {p['num']} - {p['name']}", "",
        clean(p["desc"], 2000), "",
        f"**Priority class:** {cls} ([what the classes mean](../README.md))" if cls else "",
        "", "## The steps", "",
        "Read top to bottom. Boxes inside a phase marked parallel run side by "
        "side; the others run in order. The yellow box lists where the "
        "playbook stops for you; the red box, when it does not start or "
        "stops instead.", "",
        playbook_diagram(p), "",
        "- [SKILL.md](SKILL.md) - the full playbook: preconditions, intents, "
        "proof of done for each step", "",
        "*Generated by `tools/gen_diagrams.py` from the playbook data; edit the "
        "data or the generator, not this file.*", ""])


PRIORITY = json.load(open(os.path.join(ROOT, "identity", "priority.json")))


def class_names():
    names = {}
    doc = PRIORITY.get("_doctrine", "")
    for m in re.finditer(r"class (\d) = (.*?)(?=,\s*(?:and\s+)?class \d =|\.\s|\.$|$)", doc):
        names[int(m.group(1))] = m.group(2).strip()
    return names


def priority_map():
    names = class_names()
    by = {}
    for p in PB:
        by.setdefault(PRIORITY["classes"].get(p["num"], 0), []).append(p)
    lines = ["```mermaid", "flowchart LR"]
    for c in sorted(by):
        title = f"Class {c}" + (f" - {clean(names[c], 60)}" if c in names else "")
        lines += [f'    subgraph C{c}["{title}"]', "        direction TB"]
        nodes = [f'{p["num"]}["{p["num"]} {clean(p["name"], 40)}"]' for p in by[c]]
        lines.append("        " + " ~~~ ".join(nodes))
        lines.append("    end")
    if len(by) > 1:
        lines.append("    " + " ~~~ ".join(f"C{c}" for c in sorted(by)))
    lines.append("```")
    return "\n".join(lines)


def playbooks_index():
    rows = [f"- [{p['num']} {p['name']}]({p['num']}-{p['slug']}/README.md)" for p in PB]
    return "\n".join([
        "# Playbooks", "",
        "Each playbook is a fixed route through the agents for one kind of "
        "work. When two playbooks need the same agent at once, the lower class "
        "number goes first; the other waits on a siding, nothing is dropped "
        "(`identity/priority.json`).", "",
        priority_map(), "",
        "*Left to right: class 1 goes first when two playbooks need the same agent.*", "",
        *rows, "",
        "*Generated by `tools/gen_diagrams.py`; edit the data or the generator, "
        "not this file.*", ""])


# ------------------------------------------------------------ real runs
def capture(test):
    from dispatcher import core
    mods = [importlib.import_module(f"{TESTS}.{os.path.basename(f)[:-3]}")
            for f in sorted(glob.glob(os.path.join(ROOT, TESTS, "test_playbooks_*.py")))]
    mod = next(m for m in mods if hasattr(m, test))
    events = []
    orig = core.AuditLog.append

    def spy(self, kind, record, *a, **k):
        if isinstance(record, dict):
            events.append({"kind": kind, "from": record.get("from_agent"),
                           "to": record.get("to_agent"), "intent": record.get("intent"),
                           "payload": record.get("payload") or {}})
        return orig(self, kind, record, *a, **k)

    core.AuditLog.append = spy
    try:
        with tempfile.TemporaryDirectory() as tmp:
            getattr(mod, test)(tmp)
    finally:
        core.AuditLog.append = orig
    return events


def sender_of(intent):
    s = {x for r in ROUTES if r["intent"] == intent for x in r["senders"]}
    return s.pop() if len(s) == 1 else None


def run_diagram(events):
    steps = []
    for e in events:
        k, intent = e["kind"], e["intent"]
        if k == "envelope.persisted" and intent not in ROUTINE:
            frm, to = e["from"], e["to"]
            frm = "human" if frm == "queue" else frm
            to = "human" if to == "queue" else to
            text = phrase(intent, frm, to)
            if intent == "clarification.request" and e["payload"].get("reason"):
                text = "asks you - " + clean(e["payload"]["reason"], 50)
            steps.append(["msg", frm, to, text, 1])
        elif k == "absolute_signal.hold" and sender_of(intent):
            steps.append(["note", sender_of(intent), "Held - waits for your signed release"])
        elif k == "disclosure.authorized" and sender_of(intent):
            steps.append(["msg", "human", sender_of(intent), "you sign the release", 1])
    folded = []
    for s in steps:
        if folded and s[0] == "msg" and folded[-1][0] == "msg" and folded[-1][1:4] == s[1:4]:
            folded[-1][4] += 1
        else:
            folded.append(s)
    order = []
    for s in folded:
        for who in ((s[1], s[2]) if s[0] == "msg" else (s[1],)):
            if who and who not in order:
                order.append(who)
    order = [o for o in order if o == "human"] + \
            [o for o in order if o not in ("human", "external")] + \
            [o for o in order if o == "external"]
    alias = {o: "B" if o == "human" else "X" if o == "external" else f"A{o}" for o in order}
    lines = ["```mermaid", "sequenceDiagram", "    autonumber"]
    for o in order:
        lines.append(f"    {'actor' if o == 'human' else 'participant'} {alias[o]} as {clean(label(o), 50)}")
    for s in folded:
        if s[0] == "msg":
            times = f" (x{s[4]})" if s[4] > 1 else ""
            lines.append(f"    {alias[s[1]]}->>{alias[s[2]]}: {clean(s[3], 80)}{times}")
        else:
            lines.append(f"    Note over {alias[s[1]]}: {clean(s[2], 80)}")
    if len(lines) == 3:
        lines.append(f"    Note over {alias.get('human', 'B') if order else 'B'}: no routed messages in this run")
    lines.append("```")
    return "\n".join(lines)


# ------------------------------------------------------------ pages
def team_map():
    lines = ["```mermaid", "flowchart LR",
             f'    B(["{clean(HUMAN)}"])',
             '    H{{"00 Dispatcher hub<br/>carries and logs every message"}}',
             '    B -- "signed decisions and settings" --> H',
             '    H -- "questions, holds, reports" --> B',
             '    subgraph AG["The agents - each owns one job"]', "        direction TB"]
    for aid in sorted(AGENTS):
        lines.append(f'        A{aid}["{clean(label(aid), 50)}"]')
    lines += ["    end", "    H <--> AG",
              f'    X[/"{OUTSIDE}"/]',
              '    H <-- "only on open lanes; anyone but the party you serve waits for your release" --> X',
              f"    {YOU}", "    classDef hub fill:#1f6feb,stroke:#1f6feb,color:#ffffff", f"    {OUTC}",
              "    class B you", "    class H hub", "    class X out", "```"]
    return "\n".join(lines)


def outbound_map():
    lines = ["```mermaid", "flowchart LR"]
    for i, r in enumerate(x for x in ROUTES if "external" in x["receivers"]):
        s = r["senders"][0]
        aud = r.get("audience", "counterparty")
        lines.append(f'    S{i}["{clean(label(s), 40)}<br/>{clean(phrase(r["intent"], s, "external"), 50)}"]')
        if aud == "principal":
            lines.append(f'    S{i} -- "to the party you serve" --> OK{i}["Sent"]')
            lines.append(f"    class OK{i} ok")
        else:
            lines.append(f'    S{i} -- "to the {aud}" --> HD{i}["Held until you sign the release"]')
            lines.append(f"    class HD{i} you")
    lines += [f"    {YOU}", f"    {OK}", "```"]
    # classDef must come before use is not required by mermaid; keep order stable
    return "\n".join(lines)


def seams_map(text):
    m = re.search(r"^## Seams\n\n\|.*\n\|[-| ]+\|\n((?:\|.*\n)+)", text, re.M)
    if not m:
        return None
    lines = ["```mermaid", "flowchart LR", '    H{{"Hub and agents"}}']
    for i, row in enumerate(m.group(1).strip().split("\n")):
        cells = [c.strip() for c in row.strip("|").split("|")]
        name, direction, serves = cells[0], cells[1].upper(), cells[2]
        sealed = len(cells) > 4 and cells[4].upper().startswith("YES")
        node = f'N{i}["{clean(name, 40)}' + ("<br/>(sealed)" if sealed else "") + '"]'
        words = clean(serves, 45)
        if direction == "OUT":
            lines.append(f'    H -- "{words}" --> {node}')
        elif direction == "IN":
            lines.append(f'    {node} -- "{words}" --> H')
        else:
            lines.append(f'    H <-- "{words}" --> {node}')
    lines += ["    classDef hub fill:#1f6feb,stroke:#1f6feb,color:#ffffff", "    class H hub", "```"]
    return "\n".join(lines)


GO_LIVE = f"""```mermaid
flowchart LR
    D["1 Dark run<br/>read-only inbound,<br/>every outbound seam off"] --> C["2 Compare<br/>the books against your<br/>existing process"]
    C --> R["3 Ratify tables<br/>no UNRATIFIED TEMPLATE<br/>loads in live mode"]
    R --> S["4 Staged outbound<br/>one seam at a time,<br/>lowest risk first"]
    S --> LIVE(["Live"])
    S -. "5 rollback is config:<br/>disconnect the seam,<br/>history kept" .-> C
    {OK}
    class LIVE ok
```"""

INSTALL_MAP = f"""```mermaid
flowchart LR
    F["The 15 agent folders<br/>00-dispatcher ... 14-...<br/>each a SKILL.md"] --> H1["A skills-capable host<br/>Claude, Codex, Gemini, Copilot, Hermes"]
    F --> RT["The dispatcher runtime<br/>dispatcher/ in this repo"]
    H1 --> R1["Role text only:<br/>no routing, envelopes or queues"]
    RT --> R2["The governed swarm:<br/>closed track, signatures,<br/>holds, audit log"]
    {OK}
    class R2 ok
```"""

LOOP = f"""```mermaid
flowchart LR
    RUN["A playbook run"] --> REP["After-action report<br/>one file per run"]
    REP --> DS[("The dataset")]
    DS --> DEV{{"A deviation that<br/>keeps recurring?"}}
    DEV -- yes --> PA["Playbook change proposed<br/>to you - never self-amended"]
    DS --> AMB{{"The same ambiguity hold<br/>at the same crossing?"}}
    AMB -- yes --> TU["New decision tuple<br/>proposed for you to ratify"]
    DS -. "only batches you release" .-> LEARN["Platform learning"]
    {YOU}
    class PA,TU you
```"""

CONFIG_FLOW = f"""```mermaid
flowchart LR
    T["Config table ships as an<br/>UNRATIFIED TEMPLATE"] --> E["You edit it to<br/>your site's reality"]
    E --> RAT["You ratify it:<br/>status line, date, sign-off"]
    RAT --> LD["Loaded in live mode"]
    T -. "still a template" .-> NO["Fails closed at load"]
    {OK}
    {STOP}
    class LD ok
    class NO stop
```"""

MCP = """```mermaid
flowchart LR
    HOST["Host app<br/>Hermes, OpenClaw, Claude Desktop"] -- "four tools only" --> T["identity.describe<br/>identity.submit<br/>identity.authority<br/>identity.audit"]
    T --> S["identity_mcp server<br/>refuses to start unless the track,<br/>the signature check and the log are intact"]
    S --> H{{"Hub"}}
    H --> AG["this identity's agents"]
    S -. "signs for the host only<br/>with --demo-signing" .-> H
```"""


def tests_flow(text):
    heads = re.findall(r"^## (Setup.*|Test \d+ - .+)$", text, re.M)
    if len(heads) < 2:
        return None
    ids = [f"T{i}" for i in range(len(heads))]
    lines = ["```mermaid", "flowchart LR"]
    for i, h in zip(ids, heads):
        lines.append(f'    {i}["{clean(h, 40)}"]')
    for a, b in zip(ids, ids[1:]):
        lines.append(f"    {a} --> {b}")
    lines.append("```")
    return "\n".join(lines)


def page_blocks():
    """(relative file, anchor regex, mermaid, caption) for each picture."""
    out = []

    def have(rel):
        return os.path.exists(os.path.join(ROOT, rel))

    team_cap = ("*Every arrow goes through the hub, and only on lanes in "
                "`identity/routes.json`. Each agent's own picture is in its "
                "folder; each playbook's in `playbooks/`.*")
    out.append(("README.md", r"^## What this is for$", team_map(), team_cap))
    out.append(("README.md", r"^## Outbound messages$", outbound_map(), None))
    out.append(("ROSTER.md", r"^# .*Roster.*$", team_map(), team_cap))
    out.append(("DEPLOY.md", r"^## Go-live doctrine: shadow mode first$", GO_LIVE, None))
    out.append(("INSTALL.md", r"^# Installing .*$", INSTALL_MAP, None))
    out.append(("AFTER_ACTION.md", r"^## Learning loop \(the point of all this\)$", LOOP, None))
    integ = strip(open(os.path.join(ROOT, "INTEGRATIONS.md")).read())
    sm = seams_map(integ)
    if sm:
        out.append(("INTEGRATIONS.md", r"^## Seams$", sm,
                    "*Every seam connects through an adapter that presents to the hub "
                    "as a registered endpoint. No adapter code ships in this repo.*"))
    if have("docs/TUNING_MANUAL.md"):
        out.append(("docs/TUNING_MANUAL.md", r"^## TOP OF LIST.*$", CONFIG_FLOW, None))
    if have("docs/START_HERE.md"):
        out.append(("docs/START_HERE.md", r"^# Start Here.*$", team_map(), team_cap.replace("folder;", "folder (`../NN-*/README.md`);")))
    for rel in ("docs/MOUNTING.md", "docs/SERVING_HERMES_OPENCLAW.md"):
        if have(rel):
            anchor = r"^## The four tools$" if rel.endswith("MOUNTING.md") else r"^# Serving Hermes.*$"
            out.append((rel, anchor, MCP,
                        "*The host never routes inside the swarm. There is no release "
                        "tool: releasing a held message needs your own signature.*"))
    if have("docs/OPERATOR_TESTING_MANUAL.md"):
        tf = tests_flow(strip(open(os.path.join(ROOT, "docs/OPERATOR_TESTING_MANUAL.md")).read()))
        if tf:
            out.append(("docs/OPERATOR_TESTING_MANUAL.md", r"^# Operator Testing Manual.*$", tf, None))
    for rel in ("docs/PLAYBOOKS.md", "docs/WHAT_SUCCESS_MEANS.md"):
        if have(rel):
            out.append((rel, r"^# .*$", priority_map(),
                        "*Each playbook's steps are drawn in its folder: `playbooks/PNN-*/README.md`.*"))
    if have("docs/JOB_DESCRIPTIONS.md"):
        out.append(("docs/JOB_DESCRIPTIONS.md", r"^# Job Descriptions.*$", team_map(), team_cap))
    return out


# ------------------------------------------------------------ assemble
def place(body, name, anchor, mermaid, caption):
    m = re.search(anchor + r"\n", body, re.M)
    assert m, f"no line matches {anchor!r} for {name}"
    block = (f"<!-- diagram:{name} - drawn by tools/gen_diagrams.py; edit the generator, not here -->\n"
             f"{mermaid}\n" + (f"\n{caption}\n" if caption else "") + f"<!-- /diagram:{name} -->\n")
    return body[:m.end()] + "\n" + block + body[m.end():]


def strip(body):
    return re.sub(r"\n<!-- diagram:([A-Za-z0-9-]+) - drawn by[^\n]*-->\n.*?<!-- /diagram:\1 -->\n",
                  "", body, flags=re.S)


def build():
    files = {}
    playbooks_for = {}
    for p in PB:
        for _title, rows in p["phases"]:
            for row in rows:
                if row[1] in AGENTS:
                    lst = playbooks_for.setdefault(row[1], [])
                    if (p["num"], p["name"], p["slug"]) not in lst:
                        lst.append((p["num"], p["name"], p["slug"]))
    for aid, d in agent_dirs().items():
        files[os.path.join(d, "README.md")] = agent_readme(aid, os.path.basename(d), playbooks_for)
    for p in PB:
        files[os.path.join(ROOT, "playbooks", f"{p['num']}-{p['slug']}", "README.md")] = playbook_readme(p)
    files[os.path.join(ROOT, "playbooks", "README.md")] = playbooks_index()

    pages = {}
    for rel, anchor, mermaid, caption in page_blocks():
        path = os.path.join(ROOT, rel)
        if path not in pages:
            pages[path] = strip(open(path).read())
        words = re.sub(r"[^a-z0-9]+", "-", re.sub(r"\\.", "", anchor).lower()).strip("-")[:30].strip("-")
        name = re.sub(r"[^a-z0-9]+", "-", rel.lower()).strip("-")[:-3] + "-" + words
        pages[path] = place(pages[path], name, anchor, mermaid, caption)

    pbp = os.path.join(ROOT, "docs", "PLAY-BY-PLAY.md")
    if RUNS and os.path.exists(pbp):
        body = pages.get(pbp) or strip(open(pbp).read())
        cache = {}
        for p in PB:
            test = RUNS.get(p["num"])
            if not test:
                continue
            if test not in cache:
                cache[test] = run_diagram(capture(test))
            body = place(body, f"run-{p['num'].lower()}", rf"^## {p['num']} - .*$", cache[test],
                         f"*One recorded run of `{test}`, numbered in order. Left out: "
                         "each agent logging to the record and reporting what it is "
                         "waiting on. The ratified steps: "
                         f"[playbooks/{p['num']}-{p['slug']}](../playbooks/{p['num']}-{p['slug']}/README.md).*")
        pages[pbp] = body
    files.update(pages)
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    files = build()
    stale = [p for p, b in files.items() if not os.path.exists(p) or open(p).read() != b]
    if FALLBACKS:
        print(f"note: no plain words found for {sorted(FALLBACKS)}; drawn as the intent name")
    if args.check:
        for p in stale:
            print(f"stale diagram: {os.path.relpath(p, ROOT)}")
        print(f"gen_diagrams --check: {len(files)} files, {len(stale)} stale")
        return 1 if stale else 0
    for p in stale:
        open(p, "w").write(files[p])
    print(f"gen_diagrams: {len(files)} files, {len(stale)} written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
