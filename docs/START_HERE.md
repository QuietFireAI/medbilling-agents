# Start Here - 60 Seconds

**What this is:** a 14-agent medical-billing swarm on a closed track. One
hub routes everything; only pre-approved (sender, intent, receiver) tuples
are legal; every action lands on a hash-chained, tamper-evident audit log.

**What it does:** charge capture, eligibility facts, scrubbing, prior-auth
packaging, submission (both acks or it didn't happen), posting with
contract citations, two-lane denial triage, A/R follow-up, the published
patient sequence, filing clocks, credit-balance/refund compliance, records
requests, and the daily books.

**What it never does:** code, appeal, diagnose, promise coverage, read
clinical content, move unsigned money, pressure a patient past the
published sequence, or let a denial or a clock die quietly. Each of those
is enforced in code and proven by a test.

**See it work (2 minutes):**
```
git clone https://github.com/QuietFireAI/medbilling-agents.git
cd medbilling-agents && pip install -r requirements.txt
python3 tools/run_demo.py        # one patient, six acts, real hub
python -m pytest tests_medbilling/   # every playbook, every gate
```

**Read next:** WHAT_SUCCESS_MEANS.md (what each playbook delivers and
what the human still owns) -> PLAY-BY-PLAY.md (every step narrated) ->
JOB_DESCRIPTIONS.md (one entry per agent) -> OPERATOR_TESTING_MANUAL.md
(the filmable test script) -> TUNING_MANUAL.md (every knob and every
honest placeholder).
