# V5 acceptance traceability

| AC | Implementation | Local evidence | Remaining gate |
|---|---|---|---|
| 01 | optional `project.program_id` | Addon installs and standalone projects remain valid | Verify existing project/task IDs on a representative database |
| 02 | company constraints | Cross-company ORM rejection test passes | Multi-company UI and representative data upgrade |
| 03 | milestone goal units | Goal unit is explicit; no aggregate field is implemented | Add/verify three-unit acceptance cases against V5 source |
| 04 | milestone versions | Revision and validated-value immutability tests pass | Verify target/history behavior against V5 source |
| 05 | measurement and progress | Zero, absent, over-100%, decrease and correction tests pass | Broader boundary cases from V5 source |
| 06 | explicit review publication | Portal excludes draft/internal notes/evidence notes | Attachment and browser checks |
| 07 | individual membership gate | Own/foreign project details and revocation are tested | Two-participant counts and browser checks |
| 08 | advisor memberships | Advisor reaches two allowed projects; third project is denied | Advisor revocation and browser checks |
| 09 | native sharing audit | Standard project, sharing, task and token routes are denied | Follower/collaborator and target-data audit after revocation |
| 10 | task state `1_done` | Completed vs cancelled session computation is tested | Assert no goal auto-validation through the task workflow |
| 11 | copy isolation | Project membership/review and milestone measurement history do not copy | Verify all people/assignment behavior against V5 source |
| 12 | module update | Local module upgrade with addon tests passes | Fresh install and staging upgrade with record-preservation evidence |

The external V5 specification/proposal require Google authentication in this environment, so source-specific acceptance details could not be independently checked. Local results are not staging or client acceptance. No unchecked remaining gate is accepted for deployment or production review.
