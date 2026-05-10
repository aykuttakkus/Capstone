# Phase 9 Final Freeze and Demo Rehearsal

## Purpose

Lock the project and verify the final advisor-facing demo flow one last time.

## Final Freeze Rules

- no new features
- no major UI redesigns
- no paid infrastructure
- no fine-tuning
- only bug fixes, rehearsal, and packaging

## Demo Rehearsal Checklist

1. start backend and frontend
2. confirm `/health` and `/ready`
3. run the demo script from `docs/demo_package.md`
4. verify onboarding, chat, session restore, refusal, and safety
5. verify Docker Desktop and compose still work
6. verify CI and local tests are still green

## Exit Criteria

- the demo can be rehearsed from a clean start
- no unresolved delivery gaps remain
- the final submission posture is frozen

## Verification Result

- phase 8 documentation package is in place
- phase 9 smoke coverage already exists
- backend and frontend startup paths are documented
- full backend suite passed (`66 passed`)
- frontend lint/build passed
- compose config passed
