# Project Program Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans task by task.

**Goal:** Deliver a reusable Odoo 19 app for AE and FACODI.
**Architecture:** Five generic models extend Project; guarded lifecycle methods and a curated read-only portal.
**Tech Stack:** Odoo 19 Community, Python, PostgreSQL 16, XML/QWeb, Docker, GitHub Actions.
**Spec:** docs/superpowers/specs/2026-10-14-project-program-design.md

## Global Constraints
Odoo 19 Community; module project_program; application=True; no core changes; generic names.
Never expose internal notes, attachments, unpublished values or other projects through portal.

## Review Focus
1. Cross-project/company relations must fail on create and write.
2. State injection via RPC/context must not bypass validation or immutability.
3. Membership dates, archive and revocation must apply on every request, without cron lag.
4. Standard tokens/followers must not bypass the program portal boundary.
5. Templates and copies must not duplicate members, measurements or published reviews.

### Task 1: App installation and domain models
Files: project_program/models/{program,project,membership,goal,measurement,review}.py; tests/test_models.py.
Interfaces: project.program; project.project.program_id; action_activate/close; action_validate; action_revision.
- [ ] Run registration contract against empty module (expected failure).
- [ ] Write tests for lifecycle, validation, cross-company relations, immutable history and copies.
- [ ] Implement models, ACLs and record rules.
- [ ] Run install tests and fix until green; commit.

### Task 2: Portal and native views
Files: controllers/portal.py; views/*.xml; tests/test_portal.py.
Interfaces: /my/programs and /my/programs/<project_id>; membership authorizes curated published snapshots.
- [ ] Test unpublished/internal data absence, unrelated contacts, direct IDs, token bypass and revocation.
- [ ] Implement summary projection, controller and native app views.
- [ ] Run HTTP tests and install/upgrade validation; commit.

### Task 3: Reusable presets and operational delivery
Files: wizard/program_setup.py; i18n/pt_PT.po; docs/; compose.yml; tests/test_presets.py.
Interfaces: setup wizard creates AE or FACODI program with clean project/tasks/goals and no real people.
- [ ] Test both presets, clean copy and task session state handling.
- [ ] Implement wizard, examples, translations and operating instructions.
- [ ] Run full integration/HTTP suite and upgrade; commit.

### Task 4: Final review and publication
- [ ] Request one independent whole-branch code/security review.
- [ ] Reproduce important findings in tests and fix; run full CI.
- [ ] Publish PR with explicit scope, runtime evidence and limitations.
