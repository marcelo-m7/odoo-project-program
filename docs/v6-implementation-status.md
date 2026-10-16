# V6 implementation status (2026-10-16)

Branch: `feat/v6-is-program-core`, based on `main` to avoid silently modifying historical V5 code.

## Delivered as source

- Native `project.project.is_program` feature switch (off by default).
- Project contact links `program_mentor_id` and `program_mentee_id` to `res.partner`.
- Additive backend project form and filtered “Programs” menu.
- Task `is_program` related Boolean and independent persisted `program_objective` / `program_followup` values.
- Conditional Program pages on the internal task form and the **actual** Project Sharing form (`project.project_sharing_project_task_view_form`).
- Project portal read-only Mentor/Mentorando summary for authorized standard project route visitors.
- Server-side protection against portal writes to program project configuration and protected task fields.
- Minimal TransactionCase regression coverage.

## Deliberately not changed

- Odoo's standard project collaborator ACL, task follower access, share access modes, files, messaging, milestones, reporting or route controllers.
- Existing database or current Odoo Online client instance.
- V5 models/data and security modules. The V5 implementation remains in `feat/project-program-v5` and must be migrated explicitly; **do not install V6 as an in-place upgrade of an installed V5 addon** until the migration script and database rehearsal are complete.

## Outstanding acceptance gates

1. Run `odoo-bin -i project_program --test-enable --stop-after-init` on clean Odoo 19 with PostgreSQL, then `-u project_program` and repeat.
2. Browser E2E in shared project as portal Mentor and Mentorando, including read, limited-edit and edit share modes, a non-program project and a revoked collaborator.
3. Prove portal inability to write the protected fields using direct RPC and no accidental exposure of contacts/attachments/tokens.
4. Rehearse any V5 -> V6 migration against a **copy** of the target database and preserve identities, relations, discussions and access tokens.
5. Verify addon deployment prerequisites (target hosting and Odoo.sh plan/licensing) and client acceptance.

The code is **not deployment-verified**. Source-only PR, no claim of complete E2E implementation.
