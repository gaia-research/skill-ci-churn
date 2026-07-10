# ci-churn

> **GitHub Actions cost analyzer & flaky-test detector for pull requests**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Part of Gaia](https://img.shields.io/badge/part%20of-Gaia%20skill--tree-6b46c1)](https://gaiaskilltree.com)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-3776ab.svg)](https://www.python.org)
[![Zero deps](https://img.shields.io/badge/deps-stdlib%20only-success)](#requirements)

**How much GitHub Actions rebuild time did your last PR waste on avoidable lint and test failures?**

> Golly, boss — your green build is a magician; `ci-churn` shows the sleeves.

You ship a 3-line fix, then spend the next 20 minutes watching red X's turn green one push at a time. `ci-churn` reads your PR's commit history and GitHub Actions run durations and tells you exactly where that time went — and which local pre-push check would have saved it.

No pip. No npm. No config file. One Python script, `gh` CLI, done.

---

## Quick Start

### 1. Install and Use as a Skill (Recommended)

`ci-churn` is designed to be installed as an AI agent skill for assistants like Claude Code, Codex, or pi. 

Run the installer to locate your agent's skills folder and install `ci-churn` automatically:
```bash
bash <(curl -sL https://raw.githubusercontent.com/gaia-research/skill-ci-churn/main/install.sh)
```

Once installed, invoke it directly within your agent conversation:
```
/ci-churn <pr-number>
```

### 2. Standalone Python Usage (Secondary)

If you are running manually without an agent, download and run the script directly:
```bash
# Download the script
curl -sL https://raw.githubusercontent.com/gaia-research/skill-ci-churn/main/ci_churn.py -o ci_churn.py

# Run on any PR
python3 ci_churn.py <pr-number>
```

**Before → After**

| Before `ci-churn` | After `ci-churn` |
|---|---|
| "The pipeline was flaky" — a story | 22m 49s of wasted GitHub Actions time — a number |
| Retries burn minutes with no attribution | Per-PR churn ratio + minute-count |
| Same lint error caught in CI every PR | Suggested pre-push checks generated from your run history |

### Troubleshooting the first run

- **`gh: command not found`** — install the [GitHub CLI](https://cli.github.com) and run `gh auth login`.
- **`Authentication required`** on private repos — `gh` needs `repo:read` scope. Run `gh auth refresh -s repo` to add it.
- **`PR not found`** — the PR number is repo-scoped. Pass `--owner myorg --repo myrepo` explicitly if your working directory doesn't match the PR's repo.
- **Python version** — needs Python 3.8+. Check with `python3 --version`.

---

## Why it exists

**GitHub Actions time waste** — the rebuild time burned on avoidable retry-pushes like lint fixes, import errors, and flaky test retries — is the metric almost no team tracks. Every codebase has commits that exist only because a 30-second local check wasn't run first. At 22+ minutes per PR across a team of ten, that's a GitHub Actions cost conversation worth having. `ci-churn` is a CI cost analyzer: it reads your PR commits and GitHub Actions run durations, identifies the unnecessary pushes, and generates the pre-push checks that would have prevented them.

Built as a first-class agent skill: any agent that reads `SKILL.md` (Claude Code, Codex, Cursor, Gemini CLI, pi) can call `/ci-churn <PR>` and get the same report a human would.

---

## What it looks like

Run it on any PR you own:

```bash
python3 .agents/skills/ci-churn/ci_churn.py 1017
```

Real output from a real PR:

```
CI Churn Report — PR #1017  (gaia-research/gaia-skill-tree)
════════════════════════════════════════════════════════

Commits: 6 total  (2 feature · 1 review-fix · 3 ci-fix)
Churn ratio: 66.7%  (4 of 6 commits were avoidable)

CI compute burned on avoidable commits : 22m 49s
CI compute on failed runs (all commits): 4m 16s
Agent blocked-wait estimate (min / max): 4m 16s / 22m 49s

Commit breakdown
────────────────────────────────────────────────────────
      SHA  Label           CI (s)  Fails  Message
─────────  ────────────  ────────  ─────  ──────────────────────────────
5f418b26b  feature              0      0  feat(intake): batch skill intake
ff99b6165  △ review-fix       187      2  fix(intake): address review findings
3f3f98776  ⚠ ci-fix           391      1  fix(prWriter): restore open_pr export
e1b612175  ⚠ ci-fix           398      0  fix(pushFromFile): lazy-import yaml
78e0028b5  ⚠ ci-fix           393      0  fix(pushFromFile): replace substring URL check

Suggested local pre-push checks
────────────────────────────────────────────────────────
  • python3 -c "from gaia_cli.main import main"  # import chain smoke test
  • python3 -m pytest tests/ -x -q --timeout=30  # fast local test gate
  • bandit -r src/ -ll                            # security lint (CodeQL class)
```

Two feature commits. Four commits of iteration drift. **22 minutes and 49 seconds of CI compute** burned on things a 30-second local check would have caught.

Every team has this problem. Almost no team measures it.

---

## Read your churn ratio

The single number that matters:

| Ratio | Signal |
|---|---|
| **0%** | Perfect — every commit was intentional feature work |
| **1–20%** | Healthy — minor CI surprises, typical for new code paths |
| **20–50%** | Elevated — pre-push checks are missing or not being run |
| **>50%** | High churn — your local dev loop isn't catching what CI catches |

Anything above 20% is a lever. `ci-churn` tells you which lever to pull.

---

## Use cases

- **Flaky test analytics** — classify failing runs as flake vs. real regression before filing a ticket.
- **PR CI cost** — quote a real minute-count when a colleague asks "was that PR expensive?"
- **Pre-push checks** — get a suggested local-check list derived from what your CI actually caught.
- **Agentic CI triage** — wire `/ci-churn` into an agent's post-PR retro to close the feedback loop automatically.
- **Pipeline health AI** — feed `--json` output into dashboards, Slack bots, or LLM judges.

---

## How commits are classified

By subject line, deterministically, first-match-wins:

| Label | What it matches | Meaning |
|---|---|---|
| `feature` | `feat(...)`, `add ...`, `refactor ...` | Intentional work — the reason the PR exists |
| `review-fix` | `per review`, `address review findings`, `apply feedback` | Fixed after human code review |
| `ci-fix` | `fix import`, `restore export`, `codeql`, `lazy-import`, `wheel smoke`, `fix ruff`, `fix mypy` … | Fixed because CI caught something a local check would have caught first |

`feature` commits are signal. Everything else is cost.

---

## Using an AI agent? Measure the blocked wait.

If you're pairing with **Claude Code**, **Codex CLI**, **Cursor**, **pi**, or any agent that writes commits, its session log records how long each turn took. Pass the log path and `ci-churn` correlates CI compute against agent wall-clock time:

```bash
python3 ci_churn.py 1017 --session-log ~/.pi/sessions/latest.jsonl
python3 ci_churn.py 1017 --session-log ~/.claude/projects/myrepo/session-abc123.jsonl
```

This answers the question that actually costs money: **"of the 90 minutes this agent spent on this PR, how many were blocked waiting on avoidable CI failures?"**

Session log paths:
- **pi** — `~/.pi/sessions/<project>/<session-id>.jsonl` (run `pi session ls`)
- **claude-code** — `~/.claude/projects/<project>/<session-id>.jsonl`

---

## Install

### One-liner (recommended)

```bash
bash <(curl -sL https://raw.githubusercontent.com/gaia-research/skill-ci-churn/main/install.sh)
```

Auto-detects your skills directory (`.agents/skills/`, `.claude/skills/`, or their home-directory equivalents). Prompts if multiple exist.

### Via [gaia](https://gaiaskilltree.com)

```bash
gaia skills install https://github.com/gaia-research/skill-ci-churn
```

### Via [`npx skills`](https://www.npmjs.com/package/skills)

```bash
npx skills install gaia-research/skill-ci-churn
```

### Manual

```bash
git clone --depth 1 https://github.com/gaia-research/skill-ci-churn .agents/skills/ci-churn
rm -rf .agents/skills/ci-churn/.git
```

### Script only (no agent)

```bash
curl -sL https://raw.githubusercontent.com/gaia-research/skill-ci-churn/main/ci_churn.py -o ci_churn.py
python3 ci_churn.py <pr-number>
```

---

## Usage

```bash
# Basic — repo auto-detected from git remote
python3 ci_churn.py <pr-number>

# Explicit repo
python3 ci_churn.py <pr-number> --owner myorg --repo myrepo

# JSON output (pipe into dashboards, Slack bots, retro docs)
python3 ci_churn.py <pr-number> --json

# With agent session log
python3 ci_churn.py <pr-number> --session-log ~/.pi/sessions/latest.jsonl
```

Exit codes: `0` success · `1` gh missing or unauth · `2` PR not found.

---

## As an agent skill

Once installed, invoke from any agent conversation:

```
/ci-churn 1017
```

The agent reads `SKILL.md`, runs the script, and returns the churn ratio, blocked-wait estimate, and suggested pre-push checks. Works in a post-ship retro, mid-PR review, or wired into `/fp-drift` to close every feature pipeline automatically.

---

## Requirements

| Requirement | Notes |
|---|---|
| **[gh CLI](https://cli.github.com)** | Must be authenticated (`gh auth status` passes). For private repo runs, needs `repo:read` scope. |
| **Python 3.8+** | stdlib only — zero `pip install` steps. |
| **GitHub PR** | Any PR you have read access to. Public or private. |

---

## Compatibility

Works with any agent or workflow that pushes commits to GitHub PRs:

| Agent | Install path | Notes |
|---|---|---|
| Claude Code | `.claude/skills/ci-churn/` | Invoke via `/ci-churn` |
| Codex CLI | `.agents/skills/ci-churn/` | Invoke via `/ci-churn` |
| Cursor | anywhere on PATH | Call via shell tool |
| Gemini CLI | anywhere on PATH | Call via shell tool |
| pi | `.agents/skills/ci-churn/` | Full session-log integration |
| CI pipeline | anywhere | `--json` output for automation |

---

## Gaia integration (optional)

`ci-churn` is part of the [Gaia Skill Registry](https://gaiaskilltree.com) — an open catalog of agent skills with evidence-backed quality ratings. If you use `gaia-cli`, you get install tracking, version management, and skill discovery alongside the registry's 200+ other skills.

You don't need Gaia to use this. The script is fully standalone.

---

## Why measure this

Because "the pipeline was flaky" and "I had to fix some CI stuff" are stories, not numbers. When the number is 22 minutes per PR across a team of ten, that's an engineering-hours conversation worth having.

Ship the fix. Measure the drift. Close the loop.

---

## How it compares

| Tool | Focus | Setup | Agent-native |
|---|---|---|---|
| **`ci-churn`** | Per-PR retry-cost + pre-push suggestions | One file, `gh` CLI, no config | Yes — invoked as `/ci-churn` |
| [BuildPulse](https://buildpulse.io) | Cross-repo flaky-test detection | SaaS, webhook install | No |
| [Trunk Flaky Tests](https://trunk.io/flaky-tests) | Test-quarantine + rerun policy | SaaS, per-repo config | No |
| Bare `gh run list --json` | Raw run metadata | Zero setup | You write the analyzer |
| GitHub Actions `workflow-run-summary` | Run history only | Zero setup | No — post-run read-only, no pre-push suggestions |
| [GitLab Insights](https://docs.gitlab.com/ee/user/analytics/) | GitLab pipeline analytics dashboard | GitLab-native, per-project config | No — GitLab-specific |
| [CircleCI Insights](https://circleci.com/docs/insights/) | Cross-workflow test-flakiness dashboard | CircleCI SaaS | No — CircleCI-specific |
| [Datadog CI Visibility](https://www.datadoghq.com/product/ci-cd-monitoring/) | Cross-CI observability + flake detection | SaaS, agent install per runner | No |
| [`act`](https://github.com/nektos/act) | Local GitHub Actions runner | Docker + config | No — reproduces CI, doesn't measure churn |

Different jobs. `ci-churn` optimizes for the "I want a number for *this* PR, right now, from my terminal, no signup" case — especially when an agent is asking.

---

## FAQ

| Question | Answer |
|---|---|
| **What's a "churn ratio"?** | `(review-fix + ci-fix commits) / total commits`. Above 20% means your local dev loop isn't catching what CI catches. |
| **How are commits classified?** | Subject-line regex, first-match-wins. `feat/add/refactor` → `feature`; `per review` → `review-fix`; `fix import`, `codeql`, `lazy-import`, `fix ruff/mypy`, etc. → `ci-fix`. See [the table above](#how-commits-are-classified). Deterministic — no LLM in the hot path. |
| **What if my commit messages don't match those patterns?** | Unmatched → `feature` (undercounts churn). Adopt conventional commits, or edit the label regexes at the top of `ci_churn.py`. |
| **How do I detect flaky tests in GitHub Actions with this?** | `ci-fix` commits that follow a failed run with no code change between attempts are flake candidates. Use `--json` to feed the raw data into a dashboard or Slack bot. |
| **What does "blocked-wait estimate" mean?** | With `--session-log`, the wall-clock time your agent sat idle while a failed CI run was in progress. The min/max bracket = failed-runs-only vs. all avoidable-commit runs. |
| **Which agents does `--session-log` support?** | `pi` (`~/.pi/sessions/`) and Claude Code (`~/.claude/projects/`). Any JSONL log with per-turn timestamps works. |
| **Does it work on private repos?** | Yes — `gh` CLI must be authenticated with `repo:read` scope. `gh auth status` is the smoke test. |
| **Does it need an API key or LLM?** | No. Pure Python stdlib + `gh`. No inference, no network calls beyond the GitHub API. |
| **Can I run it in CI?** | Yes. `--json` output + exit codes: `0` ok · `1` gh missing/unauth · `2` PR not found. Wire into a post-merge hook or agent pipeline. |
| **What about squash/rebase?** | Only commits currently on the PR branch are counted. Run before you squash if you want accurate churn. |
| **How do I install it?** | `bash <(curl -sL https://raw.githubusercontent.com/gaia-research/skill-ci-churn/main/install.sh)` — auto-detects your skills dir. |

---

## See also

- [merge overlapping agent commands](https://github.com/gaia-research/skill-fuse) — companion skill `skill-fuse` for combining Claude Code / Cursor / Windsurf commands into one.
- [`gaia-research/marketing-tasks`](https://github.com/gaia-research/marketing-tasks) — campaigns and deliverables using this skill.
- [Gaia Skill Registry](https://gaiaskilltree.com) — the open catalog this skill belongs to.

---

## License

MIT — see [LICENSE](./LICENSE).

---

<a href="https://gaiaskilltree.com"><img src="./powered-by-gaia.svg" alt="Powered by Gaia" height="28"></a>
