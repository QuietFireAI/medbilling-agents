# AFTER_ACTION.md - Run Report Schema + Learning Loop (v0.1, DRAFT - owner ratification pending)

Every playbook run (completed OR aborted) produces one after-action report,
generated from the audit log - never from agent memory. Reports accumulate in
`after-action/` as markdown: they ARE the learning dataset (Hermes-style
built-in learning consumes markdown docs; deviations become human-reviewed
spec amendments). Self-reported metrics are prohibited; the log is the only
source.

## Report template (one file per run: after-action/PNN-<run_id>.md)
- **run**: playbook id, run_id, client_context_id, started/ended (ISO-8601)
- **outcome**: completed | aborted (abort path taken, verbatim reason)
- **steps**: per step - executed?, proof-of-done artifact reference, latency
- **gates**: each gate - cleared/triggered, evidence reference
- **deviations**: any divergence from the playbook sequence, verbatim, with
  the envelope ids involved. A deviation is data, not shame - but an
  UNREPORTED deviation is a fabricated report.
- **escalations**: queue, transport time, human response time
- **errors**: raw errors, unparaphrased
- **kpis**: the DISPATCHER_CORE KPI set computed for this run
- **manners re-injections**: count and positions (fade-tracking)

## Learning loop (the point of all this)
1. Reports accumulate as the dataset.
2. Recurring deviations = the spec is wrong somewhere: playbook amendment
   proposed to the human (never self-amended - specs change by signed
   authority only).
3. Recurring ambiguity holds at the same crossing = a missing tuple: propose
   a new (crossing, answer) pair for the human to ratify into DECISIONS.md.
4. The dataset feeds platform learning (e.g., Hermes /learn) ONLY as
   human-released batches - agent-authored learnings about agent behavior are
   exactly the self-modification surface the write-approval gate exists for.

Status: v0.1 DRAFT - owner ratification pending - schema only; runtime generates the reports.
