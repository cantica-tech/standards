# Proposal: one set of code standards and linters for every repository (2026-10-09)

> The reasoning behind [STANDARDS.md](../STANDARDS.md): written as note 16 of catalyst's working notes, moved here
> 2026-10-17. Where it and `STANDARDS.md` disagree, `STANDARDS.md` is right.
>
> **Owner request, 2026-10-09.** "I need to have linting and standards for all the code developed accross all the
> project code to be centralized: look for best practices for all languages and create a proposal."
> Status: **v0.1.0 built and adopted locally (2026-10-09) with the recommended options — §9.** The owner asked to
> start at once; the §8 decisions were taken as recommended and stay open to change.

## 1. Where we stand

| Repository | Code | Formatter | Linter | Types | CI runs |
|---|---|---|---|---|---|
| catalyst | Python 82 files (stdlib only), Markdown, YAML, JSON | none | none | none | pytest; repo checks (freeze, budgets, purity, parity) |
| catalyst-ui | TypeScript 128 files, JSON, YAML, CSS/HTML | Prettier 3 | ESLint **8** (end of life) + typescript-eslint 7, legacy `.eslintrc.cjs` | `tsc` `strict` | lint, `prettier --check`, typecheck, tests, catalyst trace |
| catalyst-software-engineering | Markdown, YAML (schemas, `module.yaml`), JSON | none | none | — | none |
| cantica-tech (distribution) | release zips, Markdown, JSON | none | none | — | none |
| criterion repositories | Markdown, JSONL, JSON | — | `catalyst check` | — | `catalyst check`, integrity |

Nothing checks Markdown (249 files), YAML, GitHub workflows, shell or PowerShell. Rules exist only where one repo
happened to add them, so the same mistake is caught in one repo and not the next.

## 2. Principles

1. **One source of truth.** Every rule and tool version lives in one place; a repository holds a *thin* config that
   extends it, never a copy.
2. **Same commands everywhere.** `task lint`, `task format`, `task typecheck`, `task check` (all of them) in every
   repository, and CI calls exactly these.
3. **Formatters are not debated.** A formatter owns layout (Ruff format, Prettier); linters only flag what a
   formatter cannot fix. Autofix runs locally; CI only checks.
4. **Strict for new code, a ratchet for old code.** Full rule sets switched on; existing violations recorded once
   (per-file ignores or a baseline) and only ever shrink. CI fails on any *new* violation.
5. **Pinned, then updated by a bot.** Exact tool versions; Renovate (or Dependabot) proposes upgrades as pull
   requests, so a new rule never breaks `development` unannounced.
6. **Fast and local first.** The same checks run in the editor, in an optional pre-commit hook and in CI; each must
   finish in seconds.
7. **Product-agnostic, outside catalyst.** The standards are cantica-tech's engineering policy, not a catalyst
   feature: catalyst writes nothing into a host project but `catalyst.toml` (`13` §9) and its kernel stays
   generic. A governed project *may* cite the standards from a rule in its criterion (§7).

## 3. Best practice per language (recommended tools, 2026)

### Python (catalyst CLI, scripts, tests)

- **Ruff** for both lint and format (replaces flake8, isort, pyupgrade, Black; one fast binary).
  `target-version = "py311"`, `line-length = 120` (the code's current width).
  Rule set: `E W F I B UP SIM C4 PTH RUF PL S N` — pycodestyle, Pyflakes, import order, bugbear, pyupgrade,
  simplify, comprehensions, pathlib, Ruff's own, Pylint subset, Bandit security subset, naming. Tests relax
  `S101` (assert) and `PLR2004` (magic values).
- **Type checking: Pyright** in `standard` mode now, `strict` for new modules (the code is already annotated:
  `from __future__ import annotations` everywhere). Mypy is the alternative if a plugin is ever needed; none is.
- Keep the **stdlib-only** runtime constraint: tools are dev dependencies only (`requirements-dev.txt` or a
  `[dependency-groups] dev` in `pyproject.toml`, run with `uv run`).
- `pip-audit` is moot for a stdlib CLI; keep it for dev dependencies only.

### TypeScript (catalyst-ui packages, VS Code and Electron hosts)

- **ESLint 9+ with flat config** (`eslint.config.mjs`) and **typescript-eslint 8** `strictTypeChecked` +
  `stylisticTypeChecked` (type-aware rules: floating promises, unsafe `any`, unnecessary conditions).
  Plus `eslint-plugin-import-x` (cycles, ordering) and, for the Electron host, `eslint-plugin-security`.
- **Prettier 3** keeps formatting (already in place; `printWidth` to align with the Python width decision).
- **`tsc` strict** plus `noUncheckedIndexedAccess`, `noImplicitOverride`, `noFallthroughCasesInSwitch`,
  `exactOptionalPropertyTypes` (the last one with a ratchet: it is the noisiest).
- **Biome** is the credible single-tool alternative (lint + format, very fast) but lacks type-aware rules; keep it
  in view, do not switch now.
- `npm audit --omit=dev` (production deps) in CI; Renovate for updates.

### Markdown (≈250 files: the kernel, the module, `what-is-going-on`, criteria)

- **markdownlint-cli2** with a config matched to the house style (hard-wrapped prose, tables, `**Field:**`
  lines): headings, lists, fences, no trailing spaces; line length *off* (prose is wrapped by hand).
  Do **not** let Prettier reflow Markdown: the kernel's prose freeze (`check_frozen_surface.py`) and token budgets
  depend on stable text.
- **lychee** for links (relative links between kernel documents break silently today).
- Kernel prose rules stay where they are (freeze, budgets, purity): they are catalyst's own checks.

### YAML, JSON, TOML

- **yamllint** (relaxed preset + line length off) for `module.yaml`, schemas, workflows, Taskfiles.
- **Prettier** formats JSON/YAML in catalyst-ui (already); elsewhere `check-jsonschema` validates the files that
  have a schema: `module.yaml` against `module-manifest.schema.json`, workflows against the GitHub schema.
- **Taplo** formats and checks `pyproject.toml` / `catalyst.toml`.

### GitHub Actions

- **actionlint** (syntax, expressions, shellcheck on `run:` blocks) and **zizmor** (security: injection, excessive
  permissions, unpinned actions). Pin third-party actions to a commit SHA; least `permissions:` per job.

### Shell, PowerShell

- **ShellCheck** + **shfmt** for `.sh` and `run:` blocks; **PSScriptAnalyzer** for the one `.ps1`.

### Everywhere

- **EditorConfig** (UTF-8, LF, final newline, indent per language) — editors apply it before any tool runs.
- **gitleaks** for secrets (the UI already holds a `.env`; criteria hold user data).
- **Commit messages:** `catalyst trace` (already), unchanged.
- **Tests:** pytest (Python) and the UI's test runner stay; coverage is reported, not gated, until a baseline exists.

## 4. How to centralise: three options

| | A. Standards repository + reusable CI | B. pre-commit hooks repository | C. An aggregator (MegaLinter / Trunk) |
|---|---|---|---|
| What | `cantica-tech/standards`: the configs, the pinned versions, a reusable GitHub workflow (`workflow_call`) and a small sync script | a central `.pre-commit-hooks.yaml`; each repo pins it in `.pre-commit-config.yaml` | one tool runs ~all linters with one config |
| Config sharing | npm packages for ESLint/Prettier (`@cantica-tech/eslint-config`, `…/prettier-config`, GitHub Packages); Ruff/markdownlint/yamllint configs *synced* by `task standards:sync` (Ruff cannot extend a URL) and drift-checked in CI | hooks carry their own args; configs still copied | the aggregator's config, copied per repo |
| CI | each repo's workflow is ~5 lines: `uses: cantica-tech/standards/.github/workflows/lint.yml@vX` | pre-commit.ci or a CI step | its own action / service |
| Strength | one versioned source, explicit upgrades (`@vX`), works with Task and editors | fast local feedback | least setup |
| Weakness | one more repository to release | weak for type-aware ESLint and Pyright; local hooks are optional by nature | heavy (Docker images), opinionated, harder to ratchet; Trunk is a hosted product |

**Recommendation: A**, with pre-commit (B) as an optional local convenience fed by the same configs. Versioned like
everything else here (tags on `main`), released with the existing release workflow.

## 5. The standards repository (option A)

```text
cantica-tech/standards
├── python/ruff.toml, pyrightconfig.base.json
├── typescript/eslint-config/ (npm package), prettier-config/ (npm package), tsconfig.strict.json
├── markdown/.markdownlint-cli2.jsonc, lychee.toml
├── yaml/.yamllint.yaml   toml/taplo.toml   shell/.shellcheckrc   .editorconfig   .gitleaks.toml
├── .github/workflows/lint.yml          # reusable: detects languages, runs the matching tools
├── Taskfile.standards.yml              # lint / format / typecheck / standards:sync / standards:check
└── STANDARDS.md                        # the human-readable policy: why each rule, how to request an exception
```

Each repository then holds: `.editorconfig` and the synced configs (checked for drift), a two-line
`eslint.config.mjs` / Prettier key for TypeScript, the standard `task` targets (its own Taskfile includes
`Taskfile.standards.yml` — catalyst's *own* repositories, not a host project of catalyst), and a CI job calling the
reusable workflow. Exceptions are per-file and commented with a reason; a rule is disabled globally only in the
standards repository.

## 6. Rollout (per repository, smallest risk first)

| Phase | What | Notes |
|---|---|---|
| 0 | Create `cantica-tech/standards` v0.1 with the configs above and the reusable workflow | ½–1 day |
| 1 | EditorConfig + formatters (Ruff format, Prettier, Taplo) — one mechanical commit per repository, listed in `.git-blame-ignore-revs` | catalyst's commit is self-governance-suspended; the UI's goes through its journal (`journal adopt`) |
| 2 | Linters with a ratchet: Ruff, ESLint 9 flat + typescript-eslint strict, markdownlint, yamllint, actionlint, ShellCheck | existing violations as per-file ignores, then fixed module by module |
| 3 | Types: Pyright standard on catalyst; extra `tsc` flags on the UI | Pyright strict per new module |
| 4 | Security and hygiene: zizmor, gitleaks, SHA-pinned actions, Renovate, `npm audit` | |
| 5 | Ratchet down: remove ignores as code is touched; coverage reported in CI | ongoing |

Order of repositories: software-engineering (data only, quick), catalyst (Python, biggest gain), catalyst-ui (ESLint
9 migration), cantica-tech.

## 7. Relationship to catalyst

- These are **cantica-tech's** standards, so they live outside catalyst; catalyst's sources stay product-agnostic and
  its kernel module-agnostic.
- A project governed by catalyst can make them binding the catalyst way: a rule in its criterion (e.g. "every
  change passes `task lint`") that its artifacts target, and its CI step. Catalyst still writes nothing into the
  project for this.
- catalyst's own repo checks (prose freeze, token budgets, kernel purity, command parity) stay in catalyst: they are
  rules about the framework, not code style.

## 8. Decisions for the owner

1. **Mechanism:** A (standards repository + reusable workflow) — recommended — or B / C.
2. **Python type checker:** Pyright (recommended) or mypy.
3. **Line width:** 120 for Python and TypeScript alike (recommended; Prettier is at 80 today) or keep 80 for
   TypeScript.
4. **Strictness:** typescript-eslint `strictTypeChecked` with a ratchet (recommended) or `recommendedTypeChecked`.
5. **Scope:** include the criterion repositories (Markdown/JSON lint) or leave them to `catalyst check`
   (recommended: leave them).
6. **Repository name:** `cantica-tech/standards` (or another).

## 9. Status (2026-10-09)

**Decisions taken as recommended** (open to change): A (standards repository), Pyright, 120 columns, typescript-eslint
strict with a ratchet, criteria left to `catalyst check`, `cantica-tech/standards`.

**Built — `standards` v0.1.0** (local repository next to the others, tag `v0.1.0`, not yet on GitHub): Ruff, Pyright,
markdownlint, yamllint, Taplo, ShellCheck, EditorConfig configs; ESLint flat config (typescript-eslint
`strictTypeChecked` + `stylisticTypeChecked`), Prettier, strict tsconfig — all **synced** into a repository's
`.standards/` by `scripts/sync.py` (no npm or PyPI package to publish), the repository keeping thin configs that extend
them and hold its ratchet; `Taskfile.standards.yml` (`standards:lint|format|typecheck|sync|check`, wrappers
`lint|format|typecheck`); a reusable workflow (`lint.yml`, actions pinned to commit SHAs, tool versions pinned).
Choices made on the way: the ESLint standard is synced as `.standards/eslint-standard.mjs` (ESLint 10 takes any
`eslint.config.*` for its folder's config); markdownlint's MD038 and MD060 are off (meaningful spaces in code spans;
compact tables); lazy imports allowed in Python; ESLint's **bulk suppressions** (`eslint-suppressions.json`) are the
TypeScript ratchet.

| Repository | Adopted | Ratchet left |
|---|---|---|
| catalyst | Ruff format (79 files) + lint, Pyright, markdownlint (blank-line fixes in 28 documents; prose freeze and token budgets unchanged), yamllint, actionlint, zizmor (actions pinned, `contents: read`, no persisted credentials) | Ruff per-file ignores (51 files, mostly `subprocess.run` without `check`), 169 Pyright findings as warnings, 4 Markdown rules |
| catalyst-ui | ESLint 8 → 10 flat + typescript-eslint 8 strict (85 autofixes), Prettier at 120 (114 files), strict tsconfig, markdownlint, yamllint, actionlint, zizmor | 73 ESLint suppressions, `noUncheckedIndexedAccess` (126 sites), MD040 |
| catalyst-software-engineering | EditorConfig, markdownlint, yamllint | MD040, MD001 |
| cantica-tech | — | next |

Findings: the UI's `watcher.test.ts` and `perf.test.ts` are timing-sensitive and fail intermittently, before and after
the change (to fix separately). Next: publish `cantica-tech/standards`, call the reusable workflow from each
repository's CI, phase 4 (gitleaks, Renovate), then shrink the ratchets.
