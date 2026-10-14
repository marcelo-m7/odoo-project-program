# Project Program — implementation design

Implements the approved V5 design as an Odoo 19 Community application (`project_program`).
One Program groups standard projects; projects retain standard tasks. No edition model.
Five new models: program, membership, goal, measurement, review. Generic participants and
advisors serve AE mentoring and FACODI learning/content programs without coupling either platform.

## Behaviour
- Program dates, owner, company and draft/active/closed lifecycle.
- Per-project members with role, lead advisor and effective dates. Explicit individual identity.
- Numeric goals with baseline, target, unit and direction. Revisions preserve history.
- Measurements are manual with internal evidence; validation freezes values.
- Periodic reviews validate measurements and freeze a public summary before publication.
- Tasks classify action/session/workshop/review and optionally reference Calendar events.
- Portal reads published summaries only. No raw model RPC access, internal notes or attachments.
- Internal managers control all programs in allowed companies; users only their coordinated programs/projects.

## Security decision
Standard program projects/tasks remain internal for portal users, including native token routes.
The app never auto-subscribes members or creates standard collaborators. Existing non-program
projects are unaffected. This is the least-privilege implementation of V5's read-only portal:
revocation closes summary access immediately and there is no additional native grant to revoke.
Existing public attachment tokens must be audited before enrolling an existing shared project.
Curated portal dictionaries are built only after an active membership check; narrow sudo is
used for this projection, never to return raw business records or allow writes.

## Delivery
Dedicated Programs app menu, native views/search/reporting, AE and FACODI opt-in presets,
pt_PT translations, reproducible Docker development/test setup, model and HTTP regression tests,
installation and upgrade CI, operator/developer/security documentation.
No production deployment, email sending, external integration or live customer data is involved.

## Acceptance
Company isolation, individual membership (not commercial partner), expiry/revocation, immutable
validated records, zero/missing/>100% progress, goals with decreasing targets, cancelled sessions
excluded, clean template duplication, hostile IDs/tokens rejected, install and upgrade passing.
