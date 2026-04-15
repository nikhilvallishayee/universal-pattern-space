# Contributing to GödelOS

Contributions are welcome. They are welcome in the sense that a demanding editor welcomes a promising manuscript — with genuine interest in the work and no hesitation whatsoever about returning it if it does not meet the standard.

---

## The Intellectual Obligation

GödelOS operates at the frontier of a field that is, frankly, not short of charlatans. The gap between what AI systems *are* and what enthusiastic press releases *claim they are* is a chasm across which a great deal of reputational currency has been recklessly thrown. This project's commitment is to the opposite approach: to claim only what is measured, to distinguish implemented features from aspirational ones, and to treat the reader — and the code — as capable of handling the truth.

Contributors are expected to share this commitment.

---

## Development Workflow

1. **Read the relevant issue** before writing a line of code. If no issue exists for the work you intend to do, create one.
2. **Create a branch**: `git checkout -b feat/your-feature` or `fix/your-fix`
3. **Write tests before, or alongside, the implementation** — not after, when the temptation to make the tests fit the code is at its strongest
4. **Run the full suite** before opening a pull request: `pytest tests/ -v`
5. **Format the code**: `black . && isort .`
6. **Open the pull request** with a clear description, a link to the issue, and an explanation of the approach taken — not merely of the result achieved

---

## Code Standards

| Language | Standard |
|----------|----------|
| Python | PEP 8, formatted with `black`, sorted with `isort`, type-checked with `mypy` |
| Svelte/JS | Standard JavaScript; components named in `PascalCase` |
| Commits | Imperative mood, scoped: `feat(core): implement phi calculator` |

---

## Commit Format

```
<type>(<scope>): <short description>

Types:  feat, fix, docs, test, refactor, infra, chore
Scopes: core, backend, frontend, tests, wiki, infra

Examples:
feat(core): implement IIT phi calculator with partition-based approximation
fix(tests): resolve stale assertions in test_knowledge_store after interface refactor
docs(wiki): rewrite all pages in the style of a man who means what he says
```

---

## Pull Request Requirements

- [ ] All existing tests pass — without modification to make them pass
- [ ] New functionality is covered by new tests
- [ ] No secrets or credentials committed
- [ ] Linked to an issue
- [ ] API or schema changes are documented in the PR description

---

## Issue Labels

| Label | Meaning |
|-------|---------|
| `enhancement` | New feature or improvement |
| `bug` | Something is broken in a way it should not be |
| `documentation` | Documentation only — but documentation matters |
| `research` | Theoretical or exploratory work |
| `codex` | Agent-assigned task |

---

One final observation: the best contribution one can make to a project of this kind is not a feature, however clever, but the discipline to ensure that what is already there works correctly. The 167 pre-existing test failures are a more pressing problem than any new capability. Fix what is broken before building what is new. This is good advice in engineering; it is, one suspects, good advice more generally.
