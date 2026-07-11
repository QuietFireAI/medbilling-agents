#!/usr/bin/env python3
"""verify_swarm.py - the back-of-house scaffold, formal entrypoint.

Specs do not enforce themselves because an agent read them in a .md file.
This script is the enforcement: it fails the build when the spec and the
files disagree. Run from the package root (or CI). Exit 0 = clean.

Checks:
  1. TUPLE LEGALITY - every declared agent edge (direction, intent, endpoints)
     matches a ROUTES entry. Intent-existence alone is NOT enough; the
     (from -> intent -> to) tuple must be legal. (The Agent 15 defect class.)
  2. EDGE COMPLETENESS - reverse direction: every sender/receiver ROUTES names
     must DECLARE a matching edge. (The Agent 07 vendor.request defect class.)
  3. REGRESSION - frontmatter (25 files), playbook intent legality vs ROUTES,
     envelope JSON parse, required sections.

Exemptions (documented, deliberate):
 - interaction.log: ambient logging duty; legality checked, per-agent
    declaration not required.
 - escalation.* / clarification.request / integrity.violation: any-sender
    ambient duties.
 - Untyped edge cells are warnings unless whitelisted (11's content-routed
    reply forwarding is the sole whitelist entry).
"""
import glob, json, re, sys
from generate_skills import ROUTES, AGENTS

AMBIENT = {"interaction.log"}
WILDCARD_OK = ("escalation.", )
UNTYPED_WHITELIST = {("04", "routed by content"), ("13", "receiver on most artifact intents")}
TOKENMAP = {"human": "human", "hitl": "queue", "queue": "queue",
            "external": "external", "clients": "external",
            "vendors": "external", "platforms": "external"}

def entries(intent):
    out = []
    for i, s, r, _, _ in ROUTES:
        if i == intent or (i.endswith(".*") and intent.startswith(i[:-1])):
            out.append((set(s), set(r)))
    return out

def endpoints(text):
    text = text.replace("via 00", "")  # hub is transport, never an endpoint
    toks = set(re.findall(r"\b(\d{2})\b", text))
    low = text.lower()
    for k, v in TOKENMAP.items():
        if k in low:
            toks.add(v)
    return toks

def check_tuples():
    problems, warnings = [], []
    for a in AGENTS:
        aid = a["num"]
        for row in a["edges"]:
            direction, route, _, cell = row[0], row[1], row[2], row[3]
            intents = re.findall(r"`([a-z_]+\.[a-z_.]+)`", cell)
            if not intents:
                if not any(w in cell for who, w in UNTYPED_WHITELIST if who == aid):
                    warnings.append(f"{aid} {direction}: untyped cell '{cell}'")
                continue
            eps = endpoints(route)
            for it in intents:
                ent = entries(it)
                if not ent:
                    problems.append(f"{aid} {direction} `{it}`: intent not in ROUTES")
                    continue
                if direction == "OUT":
                    if not any(aid in s or "any" in s for s, _ in ent):
                        problems.append(f"{aid} OUT `{it}`: not a legal sender")
                    elif eps and not any((eps & r) or "any" in r for _, r in ent):
                        problems.append(f"{aid} OUT `{it}` -> {sorted(eps)}: no legal receiver")
                else:
                    if not any(aid in r or "any" in r for _, r in ent):
                        problems.append(f"{aid} IN `{it}`: not a legal receiver")
                    elif eps and not any((eps & s) or "any" in s for s, _ in ent):
                        problems.append(f"{aid} IN `{it}` <- {sorted(eps)}: no legal sender")
    return problems, warnings

def check_completeness():
    declared = {}  # (aid, direction) -> set(intents)
    for a in AGENTS:
        for row in a["edges"]:
            for it in re.findall(r"`([a-z_]+\.[a-z_.]+)`", row[3]):
                declared.setdefault((a["num"], row[0]), set()).add(it)
    problems = []
    for intent, snd, rcv, _, _ in ROUTES:
        if intent in AMBIENT or intent.startswith(WILDCARD_OK) or intent in (
                "clarification.request", "integrity.violation"):
            continue
        for s in snd:
            if s in ("human", "any", "external", "queue"):
                continue
            if s == "00":
                continue
            if intent not in declared.get((s, "OUT"), set()):
                problems.append(f"ROUTES says {s} sends `{intent}`; {s} declares no OUT edge")
        for r in rcv:
            if r in ("human", "any", "external", "queue"):
                continue
            if intent not in declared.get((r, "IN"), set()):
                problems.append(f"ROUTES says {r} receives `{intent}`; {r} declares no IN edge")
    return problems

def check_regression():
    problems = []
    try:
        import yaml
    except ImportError:
        return ["pyyaml not installed"]
    skill_files = sorted(glob.glob("[0-2][0-9]-*/SKILL.md")) + \
        sorted(glob.glob("playbooks/P*/SKILL.md"))
    if len(skill_files) != 25:
        problems.append(f"expected 25 SKILL.md files, found {len(skill_files)}")
    table_intents = {i for i, *_ in ROUTES}
    for f in skill_files:
        txt = open(f).read()
        m = re.match(r"^---\n(.*?)\n---\n", txt, re.S)
        if not m:
            problems.append(f"{f}: no frontmatter"); continue
        try:
            fm = yaml.safe_load(m.group(1))
            folder = f.split("/")[-2]
            if fm.get("name") != folder:
                problems.append(f"{f}: name '{fm.get('name')}' != folder")
            if not fm.get("description"):
                problems.append(f"{f}: empty description")
        except Exception as e:
            problems.append(f"{f}: yaml error {e}")
        if f.startswith("playbooks/"):
            for it in set(re.findall(r"`([a-z_]+\.[a-z_.]+)`", txt)):
                if it not in table_intents and not any(
                        t.endswith(".*") and it.startswith(t[:-1]) for t in table_intents):
                    problems.append(f"{f}: intent `{it}` not in ROUTES")
    for f in ("00-dispatcher/SKILL.md", "02-claim-scrubbing/SKILL.md"):
        m = re.search(r"```json\n(.*?)\n```", open(f).read(), re.S)
        try:
            json.loads(m.group(1))
        except Exception as e:
            problems.append(f"{f}: envelope JSON invalid: {e}")
    for sec in ("## 1. Role", "## 3. HITL", "## 7. Anti-Fabrication"):
        for f in glob.glob("[0-2][0-9]-*/SKILL.md"):
            if sec not in open(f).read():
                problems.append(f"{f}: missing section '{sec}'")
    return problems

def check_meta_layer():
    problems = []
    import os, re as _re
    for f in ("MANNERS.md", "SWARM.md", "AFTER_ACTION.md", "DISPATCHER_CORE.md",
              "identity/IDENTITY-medical-billing-agent.md"):
        if not os.path.exists(f):
            problems.append(f"meta artifact missing: {f}")
    dirs = sorted(glob.glob("[0-2][0-9]-*/"))
    for d in dirs:
        df = d + "DECISIONS.md"
        if not os.path.exists(df):
            problems.append(f"missing tuple layer: {df}"); continue
        tuples = _re.findall(r"^- \(.+?, .+\)$", open(df).read(), _re.M)
        if len(tuples) < 4:
            problems.append(f"{df}: only {len(tuples)} tuples (min 4)")
    return problems

def main():
    t_prob, t_warn = check_tuples()
    c_prob = check_completeness()
    r_prob = check_regression()
    m_prob = check_meta_layer()
    for label, items in (("TUPLE", t_prob), ("COMPLETENESS", c_prob),
                         ("REGRESSION", r_prob), ("META", m_prob)):
        for p in items:
            print(f"FAIL [{label}] {p}")
    for w in t_warn:
        print(f"WARN {w}")
    total = len(t_prob) + len(c_prob) + len(r_prob) + len(m_prob)
    print(f"verify_swarm: {total} failures, {len(t_warn)} warnings "
          f"({len(AGENTS)+1} agents, {len(ROUTES)} routes)")
    sys.exit(1 if total else 0)

if __name__ == "__main__":
    main()
