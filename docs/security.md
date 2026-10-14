# Security model

## Internal access

Program records, memberships, measurements and reviews are available only to the Program User and Program Manager groups through ACLs. Company record rules constrain program-owned records. Program goals are standard project milestones; their workflow methods enforce the Program User group and protect validated versions. Measurement and review transitions use module-local identity sentinels rather than client-supplied context booleans, so an RPC caller cannot forge an internal transition by setting a context key.

## Portal access

Portal users have no model ACL to program data. The custom portal controller uses elevated reads only after resolving an active membership for the authenticated user's individual partner, checking the project's company against the user's allowed companies, and selecting published reviews. It returns only the project/program names and published summary/measurement values; internal notes, evidence notes, and attachments are not part of the response payload.

Global project, task and milestone record rules exclude program records from standard portal access. The standard project document-access hook also rejects program projects for non-internal users, including token-based project and task routes. Project-sharing access remains subject to Odoo's native access check.

## Local evidence

The disposable Odoo 19 database test covers:

- Own-project listing and detail access, advisor access to two projects, and denial of a third project.
- Membership revocation, unpublished/internal review content exclusion, and evidence-note exclusion.
- Standard project, project-sharing, and project/task token routes.
- Rejection of client-forged measurement validation/correction, review transition, and goal supersession context values.

This does not replace auditing followers, collaborators, existing project/task tokens, attachments, or browser behavior on the target database. Those target-specific checks and staging upgrade evidence remain open before deployment acceptance.
