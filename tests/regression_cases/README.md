# Regression Cases

When a smoke test fails, document it here.

## Structure

```
regression_cases/
├── TEST-A.wallCreate.fail.2024XXXX/
│   ├── expected.json
│   ├── actual.json
│   └── notes.md
├── TEST-B.viewport.fail.2024XXXX/
│   └── ...
```

## How to Add a Case

1. Create folder: `{TEST}-{operation}.fail.{date}/`
2. Add `expected.json` - what should have happened
3. Add `actual.json` - what actually happened
4. Add `notes.md` - root cause analysis

## Purpose

- Track failures that need fixing
- Prevent regressions
- Build test coverage over time
