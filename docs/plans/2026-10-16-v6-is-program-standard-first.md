# Project Program V6 — Standard-first refactoring plan

Status: **PROPOSED / PLANNING ONLY** (2026-10-16). Branch based on `feat/project-program-v5`. No runtime refactor or migration has been executed. Target: Odoo 19 Community initially; verify optional Enterprise/Odoo.sh integrations separately.

## 1. Decision and business rationale

A **program is an existing `project.project` record** whose `is_program = True`. It is *not* a wrapper containing multiple projects. A conventional project remains conventional by default; no separate program is required to run the Algarve Evolution pilot. This supersedes the V5 `project.program -> project.project` parent/child design, V5 dedicated restricted portal as the exclusive entry point, and specialized mandatory goal/review workflows.

The client's validated starting point is native Project, Task, Milestone, Project Sharing, followers, collaborators, task deadlines and existing reporting/sharing. Before any custom code is deployed, António completes tasks/dates; two portal accounts (mentor and mentee) are provisioned; test exact access and report-sharing behaviour. No new development is a prerequisite for this pilot. The custom code becomes available only after a compatible custom-addon hosting/deployment route is completed (planned Odoo.sh migration; verify license and deployment compatibility).

## 2. Invariants

- `project.project` is the single source of truth for the program/project identity; `project.task` for activities and meeting records; `project.milestone` for milestones; `res.partner` for people.
- `is_program` is a non-computed, indexed Boolean, default False. False must retain normal Project and Project Sharing behaviour. Switching True must not clone projects, tasks or portal users.
- Reuse `project.collaborator`, task followers, Odoo access modes, chatter, documents/attachments and standard record rules wherever possible. A project share or task share is not equivalent to being a task assignee; test all three modes.
- The flag is a **UI/feature switch, not an access-control boundary**. Never trust `is_program`, form `readonly`, hidden fields or a browser URL to enforce authorization.
- Do not expose internal fields, contacts, attachments or reports to portal accounts merely because `is_program=True`. Explicitly decide visibility and validate server-side ACL/rules and HTTP/RPC access.
- No dependency on Field Service, Studio, Enterprise or a custom API for the V6 core. Enterprise features optional/integration-specific; do not claim Odoo.sh deployments are available until confirmed.
- No automatic injection of arbitrary Studio fields into the portal. If configurable task fields are required, use an explicitly allowlisted publication configuration; protect sensitive and related fields.
- Existing projects and tasks must keep IDs, followers, shares, tokens, attachments, chatter, deadlines, time entries and external references. Migration runs transactionally, is idempotent and has dry-run/audit/rollback instructions.

## 3. Proposed minimal model

```python
class ProjectProject(models.Model):
    _inherit = "project.project"
    is_program = fields.Boolean(default=False, index=True, copy=False)
    program_mentor_id = fields.Many2one("res.partner", string="Mentor")
    program_mentee_id = fields.Many2one("res.partner", string="Mentee")
```

Naming clarification: discussion used “Mentorando” and “Mentorável” for contact fields. Confirm with the client before final migration: these may refer to the same person. Suggested **Mentor** (advisor) and **Mentorando** (participant) as distinct, user-facing labels; if both original labels represent two distinct contact roles, retain them and document semantics rather than guessing. Underlying technical names should remain stable across UI translations.

Contact fields belong to `project.project`, not `project.task`. They reference `res.partner` (including non-user contacts), are editable by authorized internal program administrators only and read-only in any portal rendering. Do not grant portal `write` to these fields via form widgets or API; since a portal collaborator may otherwise have project-level write pathways, implement tested server-side field protection appropriate to the actual ACL model. Avoid assuming `readonly="1"` enforces RPC security.

A subsequent enhancement may introduce a **project-scoped participant/role association** only if multiple mentors/mentees, replacements/history or company-specific access cannot be represented correctly by two contact references and native `project.collaborator`. Do not recreate broad V5 membership machinery preemptively. Project manager remains the native `user_id`.

Task-side data: use native `description` and `task_properties` where practical. If two program-only textual notes are justified by validation, define explicit `project.task` fields (e.g. `program_objective` and `program_followup`), shown only when `project_id.is_program`, with one persisted value per task and server-validated portal read policy. Backoffice and portal MUST reference the *same underlying field*; never duplicate values in a template.

## 4. UI contract

### Backoffice (native form inheritance)

- Project form: checkbox **Is Program**, grouped “Program” area when enabled: Mentor, Mentee, contextual program summary and a shortcut to tasks/milestones. Keep native sharing controls, descriptions, task dates and reporting.
- Task form: optional **Program** notebook page only for tasks whose project has `is_program=True`. The page is additive, inherits the existing form and does not hide or replace native pages.
- Lists/kanbans: optional filter “Programs”, program indicator, no separate top-level program entity. An app/menu “Programs” can be a filtered `project.project` action/domain, not a parallel ORM model.
- Existing projects with `is_program=False` are unaffected and retain the same controls and workflows.

### Project Sharing (the *actual* project-sharing web client)

The route `/my/projects/<project_id>/project_sharing/<task_id>` uses a dedicated `project.task` **form view** (`project.sharing.project.task.view.form`), not `project.portal_my_task` QWeb. Inherit the former to add **Program** tab only when `project_id.is_program`; keep widgets/read rights compatible with Odoo 19 and with all shared access modes. Server authorization must precede rendering. Do not rely on group visibility attributes on the *backend* Studio form.

The ordinary portal `/my/tasks/<id>` and `/my/projects/<id>` are separate QWeb routes. Consider small opt-in visual enhancements to these only where useful, and avoid accidentally modifying unrelated standard projects. When a program project is shared, standard task navigation should continue to work.

### Portal UX by profile

- **Mentor**: program overview, milestones and tasks permitted by the project's native share/follower settings, published progress/notes that the mentor is authorized to see, linked contact info only if explicitly published.
- **Mentorando**: own project overview, planned tasks/dates, comments/uploads as native share level permits, and explicitly visible summary fields.
- **Manager**: uses full internal Project interface; no forced portal redirection.
- **Unauthorised or revoked user**: no project/task/report details, including through direct URL, token, file download or guessed IDs.

Prefer native access modes (read / limited edit / edit) and native project collaborator as initial permissions. A bespoke mentor/mentee role must NOT grant access on its own; explicit collaborator status and native rules determine actual project and task visibility. If the business requires stricter confidentiality than standard project sharing offers, define a dedicated access policy and migration gate, do not silently weaken native rules.

## 5. Reports and dates

Use standard task due dates, milestones, chatter, project updates, portal attachments and existing report sharing before proposing new models. Report formats and disclosure of unpublished/internal content require explicit sign-off. If structured program reports become necessary, implement an optional separate feature later, still keyed to `project.project` and with publication workflow; avoid restoring mandatory V5 measurement/review state machines.

## 6. Existing V5 components: disposition

| Component | V6 disposition |
| --- | --- |
| `project.program`, `program_id`, `project_count` | Deprecate/remove after migration; replace with `project.project.is_program` and a filtered action |
| `project.program.membership` | Replace with native collaborator/follower first; retain a minimal project-scoped role table only if validated |
| `project.program.review`, `measurement`, versioned goals | Defer / optional extension, do not gate MVP |
| `project.milestone` extension | Preserve only validated minimal enhancements |
| `project.task` extension | Preserve task relation/data, adapt visibility to parent `is_program` |
| Custom `/my/program-projects` controller | Do not block standard portal; migrate selected UX to guarded Project Sharing and optional native portal enhancements |
| V5 security overrides blocking native portal/task/token routes | **Remove only with dedicated regression tests and audit**; preserve protections against unauthorized reads, field writes and content leakage |
| V5 tests/docs/evidence | Retain as historical reference and rewrite assertions for V6 standard-first access rules |

IMPORTANT: repository `main` currently contains only a README; implementation exists on `feat/project-program-v5` and an older `feat/project-program-app`. Do not rebase/overwrite either implementation destructively. The V6 implementation should be a new branch based on the audited V5 implementation; adopt via reviewed PR after migration gates.

## 7. Data migration and deployment

1. Inventory actual target instance before write: installed modules, `project.program`, `project.project.program_id`, project collaborator/follower/rule state, existing project names/IDs, all custom fields, attachments, token links and portal access. Capture backup and reversible export.
2. Define deterministic mapping for each former `project.program` and its child projects. **Do not set all child projects as independent programs automatically.** Get client-approved mapping: designate existing project as the program, or create a new `project.project` only when explicitly approved, retaining old project identities and linkage.
3. Reconcile partner-role mapping and metadata. If V5 projects represent participating organizations, preserve as ordinary projects or related records rather than losing them.
4. Add `is_program` initially False for existing projects; enable only approved records after preview. Handle stale V5 columns/models and external IDs with versioned pre/post-migrate scripts.
5. Do not uninstall V5 blindly: removal can delete records. Run fresh-install and in-place-upgrade tests with copied databases; log counts before/after, exceptions, revert and backup procedures.
6. Stage on Odoo 19 compatible custom-addon hosting; verify deployed commit, module upgrade, project/task access, mobile/desktop view and rollback; deployment only after two-user client validation and approval.

## 8. Delivery slices and acceptance gates

**G0 — Standard pilot (no custom code):** António finalizes tasks/dates; create mentor/mentee portal users; assign appropriate project sharing modes; exercise task views, edits, comments, milestones, reports and access revocation. Record evidence, gaps and sign-off.

**G1 — Minimal program flag:** `is_program`, filtered menu/action, two project contact fields, backoffice settings and test that ordinary projects remain unchanged. Confirm terminology Mentor/Mentorando vs Mentorando/Mentorável.

**G2 — Shared task view:** Conditional Program tab in `project.sharing.project.task.view.form`; same task values in internal/sharing views; read-only vs edit policy; show two extra fields when enabled; multiple tasks with different text values. Full test for standard task and program task, portal read/limited/edit modes.

**G3 — Program-aware project portal:** project overview and participants display when explicitly allowed; coherent task links and standard reporting. Complete negative security coverage: unrelated project, revoked collaborator, contact write via RPC, unpublished report, token routes, cross-company and attachments.

**G4 — Migration/upgrade:** dry-run on cloned real data, preserve IDs/relationships, validate counts and rollback. No forced migration from Odoo Online without operational readiness.

**G5 — Acceptance/deployment:** end-to-end in staging as mentor and mentee, desktop/mobile, performance, accessibility, log audit, screenshots, code review and client sign-off. No production merge/deploy before gate.

Each slice should have automated model tests and HTTP/portal tests plus a manual user acceptance script. Explicitly inspect Odoo 19 upstream view XML identifiers before coding.

## 9. Test matrix (minimum)

| Context | Expected |
| --- | --- |
| Ordinary project `is_program=False` | Standard native backoffice/portal, no Program tab |
| Program project `is_program=True` | Program UI appears for authorized users |
| Task A/B same program | Each renders its own persisted notes; edits sync on reload |
| Internal editor changes task field | Portal reads same persisted value (subject to authorization) |
| Portal read-only | Can read allowed fields, cannot modify program contacts or restricted notes |
| Portal limited edit | Native follower-based task scope preserved |
| Portal full edit | Native share scope preserved; protected program metadata still immutable |
| Portal user not collaborated/revoked | Cannot read via project sharing, normal portal, RPC, tokens, attachments |
| Manager changes mentor/mentee contacts | Values stored on project and reflected in permitted views |
| Multi-company, mixed visibility | No privilege escalation/leak |
| Fresh installation / V5 upgrade | No lost tasks, milestones, files, followers, or duplicate records |

## 10. Scope and estimate

Use **G0 pilot as the scope baseline**, then re-estimate development. The earlier V5 allocation of **100h (50h Corvanis-provided + 50h paid at €65/h = €3,250 for the paid block)** remains commercial historical context, *not* an approved V6 fixed quote. Do not automatically carry V5 effort estimates or promise hours/dates for an unapproved refactor. Publish per-gate effort after G0 and migration discovery.

## 11. Open decisions (must be resolved before G1/G3)

1. What exactly do “Mentorando” and “Mentorável” represent? Should the intended pairing be **Mentor** and **Mentorando**?
2. Is a program a *single project representing a mentoring cohort/startup*, or a *program containing multiple startup projects*? This V6 explicitly adopts the former as requested. If both are needed, consider native project tags or project hierarchy with clear semantics, not `project.program` by default.
3. Should any program notes be editable by portal users, or should they remain internal-only?
4. Which reports and contact fields are publishable to whom?
5. Which existing V5 data have been installed in a persistent target, and what is the migration cutover date?

## 12. Definition of done

The repository contains one Odoo 19 installable `project_program` addon extending native project, conditional on `is_program`, with no mandatory parallel program entity; non-program behaviour untouched; tests cover native share modes and security, real project/task persistence, client portal UAT and upgrade; migration and rollback instructions are reproducible. Release requires documented approvals for scope, security and deployment.
