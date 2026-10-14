# Architecture and delivery plan

Source hierarchy: V5 specification and comments (14 October 2026), V5 proposal, three V5 Lucid pages, actual Odoo 19 source. The commercial proposal is not recorded as accepted by the client.

`project.program` groups existing `project.project` records. Membership is per individual partner and project. Goals extend `project.milestone`; measurements and reviews are separate audit records. Activities extend `project.task`. The custom authenticated portal presents only explicitly published review measurements. No client data ships with the addon.

The 100 hour V5 allocation is B1 8 h, B2 18 h, B3 18 h, B4 20 h, B5 10 h, B6 14 h, B7 8 h, B8 4 h. These are planning estimates, not time logged. The security and portal block is the largest effort risk. Staging details, installation permission and client pilot data remain to be confirmed before G3/G4 acceptance.

Implementation order: core and company constraints; goal versioning and review publication; membership and server side isolation; portal; activity; install/upgrade and representative browser tests; client configuration after read only inspection of the existing reference project.

Odoo 19 source observations: `project.milestone` links project and tasks but has no numeric history; `project.task.state` distinguishes `1_done` from `1_canceled`; `project.project` uses followers and `project.collaborator`; native portal project rule uses `child_of` a commercial partner. These require explicit individual authorization for program data. Standard followers, collaborators, assignments and tokens must be inventoried on the target before treating membership revocation as complete.
