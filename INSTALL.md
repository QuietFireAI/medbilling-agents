# Installing the DispatcherAgents Medical Billing Swarm (Healthcare RCM) Skills

These 15 agent folders use the Agent Skills open standard (agentskills.io):
each folder contains a SKILL.md with YAML frontmatter (name, description) and
markdown instructions. The FILE FORMAT is identical across all supporting
platforms - do not rename SKILL.md. Only the INSTALL PATH differs per platform.

Reported install locations (verify against your tool's current docs - paths
are the one thing the standard does not pin down):

| Platform | Reported skills directory |
|---|---|
| Claude Code / Claude apps | `~/.claude/skills/` or project `.claude/skills/` |
| OpenAI Codex CLI | `.agents/skills/` (project) / `~/.codex/skills` (reported, may require enable flag) |
| Gemini CLI | Gemini's user skills directory (see current Gemini CLI docs) |
| GitHub Copilot / VS Code | VS Code agent skills location (see current docs) |
| Hermes Agent (Nous Research) | `~/.hermes/skills/` (primary), or register a shared dir (e.g. `~/.agents/skills/`) under `skills.external_dirs` in `~/.hermes/config.yaml`. Each agent loads as a `/agent-name` slash command. GOVERNANCE NOTE: Hermes agents can rewrite skills via `skill_manage`; set `skills.write_approval: true` and/or make these folders read-only so agents cannot edit their own role specs. |
| Custom runtime (DispatcherAgents dispatcher) | Anywhere - the dispatcher reads each agent's folder and injects SKILL.md content into that agent's context. Path for any model/harness without native skills support. |

Copy the agent folders (00-dispatcher ... 14-daily-operations) into the
target directory as-is. Frontmatter `name` matches each folder name per spec.

Caveats:
- These are agent ROLE definitions for a hub-and-spoke swarm, not standalone
  task skills. Loading one into a generic coding agent will give it the role
  text; the swarm semantics (routing, envelopes, queues) require the
  DispatcherAgents runtime.
- Platform-specific skill features are deliberately unused; files stick to the
  core spec for maximum portability.
- Status: v0.1 ratified 2026-07-10 (owner sign-off); runtime-tested via the dispatcher-agents suite; no licensed legal review yet.

## Pillar relationship (dispatcher runtime)

This identity contains NO pillar code and NO runtime code, by design. The
six pillars (before-turn, open-mind, agent-open-mind, pre-response-
selfcheck, sleep-marks, splitvantage) install with the DISPATCHER, not with
the identity: the dispatcher imports each pillar package and binds it to a
runtime seam, then side-loads this identity onto the closed track. Every
pillar gate that fires on the baseline null identity fires identically on
this identity's traffic - proven by the P11 demo's six-pillar assertion.
Install order: dispatcher-agents + six pillar repos first (see its
PILLAR_TESTING_MANUAL.md), capture the baseline KPIs, then load this
identity and compare.

## Deployment target (direction)

Sold configuration aims at a self-hosted appliance: Snowball-class box or a
repurposed NAS on the brokerage's network, running dispatcher-agents + the
six pillars + this identity, data on-premises. STATUS: direction, not
built. What exists today: the Python runtime + this identity + the testing
manuals. Tool bindings (MLS, CRM, email/SMS) are per-deployment work.
