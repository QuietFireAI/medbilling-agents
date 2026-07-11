# medbilling-agents - medical billing vertical for the DispatcherAgents runtime

An **identity side-load**: everything vertical-specific for a 15-agent
medical-billing (revenue cycle) swarm, loadable into the content-neutral
[dispatcher-agents](https://github.com/QuietFireAI/dispatcher-agents) runtime.
The runtime never contains vertical text; this repo never contains transport
code. That split is the architecture.

**Status: v0.1 DRAFT - owner ratification pending. Not runtime-hardened. No
licensed legal, compliance (HIPAA), or coding-practice review has been
performed.**

## What this is for

Operations support for a billing desk or billing service: charge capture with
codes as provider-entered, edit-table scrubbing with certified-human exits,
eligibility facts with timestamps, prior-auth packages for clinical
attestation, dual-artifact submission confirmation, verbatim remit posting
with contract-rule citations, deadline-tracked denial and appeal packages,
published-sequence A/R follow-up, policy-cited patient billing, the filing
clock engine, an append-only billing file, and the daily books.

What it never does - the five absolute lines (identity/IDENTITY-medical-billing-agent.md):

1. The swarm never codes - judgment exits to the certified human coder.
2. Clinical content is sealed custody (HIPAA) - moved, never read; medical
   necessity is never swarm-authored.
3. No unsigned money - write-offs and plan exceptions move only on signed
   authority.
4. No pressure beyond the published contact sequence - hardship and
   settlements are human decisions.
5. A denial never dies quietly, a clock never slips silently.

## Layout

| Path | What it is |
|---|---|
| `identity/routes.json` | The closed track: 35 (intent, senders, receivers) routes - single source of truth |
| `identity/priority.json` | JIT playbook priority classes (DRAFT) |
| `identity/IDENTITY-medical-billing-agent.md` | The identity declaration |
| `00-dispatcher/ ... 14-daily-operations/` | 15 agent SKILL.md + DECISIONS.md (tuple layer) |
| `playbooks/P01 ... P10` | Deployment playbooks: charge-to-clean-claim through EOD books |
| `SWARM.md` | Framework manifest + swarm-level tuples |
| `MANNERS.md` | Conduct constants, hash-registered at boot attestation |
| `TUPLE_INDEX.md` | Generated drill-down: tuple → agent → playbooks |
| `generate_skills.py` / `gen_meta.py` / `gen_playbooks.py` / `gen_tuple_index.py` | Generators - data tables are the spec; files are build artifacts |
| `verify_swarm.py` | Enforcement: tuple legality, edge completeness, regression - exit 0 = clean |

## Verify

```bash
python3 verify_swarm.py    # 0 failures, 0 warnings expected
```

## Load into the runtime

```bash
git clone https://github.com/QuietFireAI/dispatcher-agents.git
git clone https://github.com/QuietFireAI/medbilling-agents.git
cd dispatcher-agents && pip install -e ".[pillars,crypto,dev]"
```

```python
from dispatcher.loader import load_identity
ident = load_identity("/path/to/medbilling-agents")
```

The loader is fail-closed: no routes.json, no track, no load. It audits the
priority table's status on every load - never silently.

## Sibling identities

- [listing-agents](https://github.com/QuietFireAI/listing-agents) - real-estate listing vertical (ratified)
- [claim-agents](https://github.com/QuietFireAI/claim-agents) - insurance claims vertical (ratified)
- [reservation-agents](https://github.com/QuietFireAI/reservation-agents) - park/resort reservations vertical (ratified)
- mortgage-agents, property-mgmt-agents, practice-agents - this drop's siblings

## License

Proprietary - see LICENSE (placeholder pending legal review).
