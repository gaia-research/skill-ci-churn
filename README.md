# ci-churn

**How much CI-compute did your last PR actually burn on avoidable "fix the CI" pushes?**

You ship a 3-line fix, then spend the next 20 minutes watching red X's turn green one push at a time. `ci-churn` reads your PR's commit history and GitHub Actions run durations and tells you exactly where that time went — and which local pre-push check would have saved it.

```bash
bash <(curl -sL https://raw.githubusercontent.com/gaia-research/skill-ci-churn/main/install.sh)
```

No pip. No npm. No config file. One Python script, `gh` CLI, done.

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

## License

MIT — see [LICENSE](./LICENSE).

---

<a href="https://gaiaskilltree.com"><img src="./powered-by-gaia.svg" alt="Powered by Gaia" height="28"></a>
