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

from medbilling_playbooks import PB  # single source (fork-drift fix 2026-07-18)
def main():
    os.makedirs(ROOT, exist_ok=True)
    for p in PB:
        d = os.path.join(ROOT, f"{p['num']}-{p['slug']}")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "SKILL.md"), "w").write(build(p))
        print("emitted", p["num"])

if __name__ == "__main__":
    main()
