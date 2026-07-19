# Operator Testing Manual - Medical Billing Swarm

A filmable, step-by-step script. Every step states what you type, what
you must see, and what it proves. No step asks you to trust a claim the
screen doesn't show. Written for a billing professional to run cold.

## Setup (once)

```
git clone https://github.com/QuietFireAI/medbilling-agents.git
cd medbilling-agents
pip install -r requirements.txt
```
**You must see:** pip finish without errors.
**Proves:** the bare-clone guarantee - no hidden environment.

## Test 1 - The whole suite

```
python -m pytest tests_medbilling/ -v
```
**You must see:** `24 passed`, including tests named for every playbook
P01-P14 and for each absolute line (never-codes, sealed custody, unsigned
money rejected, $0.00 tolerance, opt-out kill, closed track).
**Proves:** the claims in the docs are executable, not aspirational.

## Test 2 - Watch one patient end to end

```
python3 tools/run_demo.py
```
**You must see, in order:**
1. ACT 1: `codes on the released claim: ['99213'] <- provider-entered,
   untouched` and `RELEASED: True`
2. ACT 2: `confirmed submissions so far: 0` after ONE ack, then 2 copies
   confirmed only after BOTH acks
3. ACT 3: the unruled CO99 adjustment HELD; a ONE-CENT variance raising
   `reconciliation.exception`; the CO50 denial lane `human_packet`; the
   60-day clock ARMED
4. ACT 4: `unsigned refund.authority -> hub says ok=False` then the
   signed one: `refund executed: executed`
5. ACT 5: `next statement attempt: 'halted_optout'`
6. ACT 6: `verify_chain(): ok=True`, `dead letters: 0`
**Proves:** the five absolute lines and the $0.00 rule under real hub
traffic - not narration.

## Test 3 - Try to break the money lane (adversarial)

Open a Python shell in the repo root and paste:
```python
import sys; sys.path.insert(0, ".")
from tests_medbilling.test_playbooks_e2e_all import build_swarm
from dispatcher.core import Envelope
hub, signer, spokes, _ = build_swarm("/tmp/adv")
env = Envelope(from_agent="human", to_agent="08",
               intent="writeoff.authority", client_context_id="adv-1",
               payload={"amount": 500.0},
               provenance={"source": "human", "captured_at": "runtime",
                           "verbatim_available": True})
print(hub.send(env))
```
**You must see:** a rejection (not ok) - a forged, unsigned $500 write-off
going nowhere.
**Proves:** `decided_by` is not a credential here; the Ed25519 signature
is. Any string can claim to be a human - only a key can prove it.

## Test 4 - Tamper with the log

```
python3 tools/run_demo.py            # note the log file path it prints
# edit any middle line of that .jsonl file - change one character - then:
python3 - <<'PY'
from dispatcher.core import AuditLog
print(AuditLog("PASTE_THE_PATH_HERE").verify_chain())
PY
```
**You must see:** `ok: False` with the violation named by line number.
**Proves:** the audit log is the single source of truth because it is
tamper-EVIDENT, not tamper-proof-by-promise.

## Test 5 - The closed track

```
python -m pytest tests_medbilling/ -k closed_track -v
```
**You must see:** the test pass - agent 03 attempting to send
`denial.intake` (a route it does not own) and being rejected.
**Proves:** no agent can improvise a new lane. The track is the law.

## What to challenge next (for the skeptical reviewer)

- Ask where COB primacy rules live -> config-driven, deployment content,
  honestly listed in TUNING_MANUAL's TOP OF LIST.
- Ask about underpayment recovery -> 08's variance detection exists
  (Test 2, Act 3); a dedicated recovery playbook is named future work.
- Ask who signed the signer registry -> a fictional test persona,
  declared in authority_signers.json itself; production replaces it.
Nothing above is hidden. The gaps are in writing next to the strengths.
