# Running Tests

The test suite is the system's immune system; and one's attitude toward it is a reliable indicator of one's seriousness as an engineer. Those who delete tests to make the suite pass, or weaken assertions to avoid confronting failures, or mock away real behaviour in order to achieve a green status indicator, are engaged in a form of self-deception that will, in the fullness of time, present its bill with compound interest.

GödelOS does not do this. The rules are stated plainly below and they are not subject to negotiation.

---

## Current Status

| Metric | Value |
|--------|-------|
| Total collectible | 1,299 |
| Collection errors | 0 |
| Passing (baseline) | 925 |
| Failing (pre-existing) | 167 → 0 (PR #74 in progress) |
| Skipped | 139 |

---

## Running the Suite

```bash
# Full suite — the definitive run
pytest tests/ -v

# Abbreviated — skip slow tests when speed is required
pytest tests/ -v -m "not slow"

# By category
pytest tests/ -m "unit"          # Fast, isolated
pytest tests/ -m "integration"   # Requires module wiring
pytest tests/ -m "e2e"           # Requires running backend on localhost:8000

# Single file — for targeted investigation
pytest tests/test_knowledge_store.py -v

# With coverage — the honest version
pytest tests/ --cov=backend --cov=godelOS --cov-report=term-missing

# Stop on first failure — useful when debugging a specific module
pytest tests/ -x
```

---

## Test Marks

| Mark | Meaning |
|------|---------|
| `@pytest.mark.unit` | Fast, isolated, no external dependencies |
| `@pytest.mark.integration` | Requires module wiring |
| `@pytest.mark.e2e` | Requires backend running on `localhost:8000` |
| `@pytest.mark.slow` | Takes more than five seconds |
| `@pytest.mark.requires_backend` | Backend must be running |

---

## Frontend Tests

```bash
cd svelte-frontend
npm test           # Playwright end-to-end tests
npm run test:unit  # Component unit tests
```

---

## The Rules

These are not guidelines. They are requirements, and violations will be caught in review.

1. **Do not delete tests.** A test that fails is telling you something; silence it and you have lost the information.
2. **Do not weaken assertions.** If `assertEqual` is failing, the problem is in the source, not in the stringency of the test.
3. **Do not mock away real behaviour** to achieve a pass. A test that passes because the real implementation has been replaced with a stub is not a passing test; it is an empty ceremony.
4. **If the source is broken, fix the source.** This is obvious. It is also, evidently, not obvious enough.
