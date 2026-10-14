from odoo.exceptions import ValidationError, UserError
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestProjectProgram(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids = [(4, cls.env.ref("project_program.group_program_manager").id)]
        cls.program = cls.env["project.program"].create({
            "name": "Reusable program",
            "user_id": cls.env.user.id,
            "date_start": "2026-01-01",
            "date_end": "2026-12-31",
        })
        cls.project = cls.env["project.project"].create({
            "name": "Participant project",
            "program_id": cls.program.id,
            "company_id": cls.program.company_id.id,
        })
        cls.goal = cls.env["project.milestone"].create({
            "name": "Revenue",
            "project_id": cls.project.id,
            "is_program_goal": True,
            "goal_unit": "EUR",
            "goal_baseline": 100,
            "goal_target": 200,
            "goal_direction": "increase",
        })

    def test_program_is_optional_and_company_is_enforced(self):
        self.program.action_activate()
        self.assertEqual(self.program.state, "active")
        standalone = self.env["project.project"].create({"name": "Standalone"})
        self.assertFalse(standalone.program_id)
        other_company = self.env["res.company"].create({"name": "Other company"})
        with self.assertRaises(ValidationError):
            standalone.write({"company_id": other_company.id, "program_id": self.program.id})

    def test_measurement_zero_decrease_and_revision_history(self):
        self.assertFalse(self.goal.has_measurement)
        self.assertEqual(self.goal.progress_percent, 0)
        measurement = self.env["project.program.measurement"].create({
            "goal_id": self.goal.id,
            "value": 0,
        })
        with self.assertRaises(UserError):
            measurement.with_context(_program_validate_measurement=True).write({"state": "validated"})
        measurement.action_validate()
        self.assertTrue(self.goal.has_measurement)
        self.assertEqual(self.goal.current_value, 0)
        self.assertEqual(self.goal.progress_percent, -100)
        with self.assertRaises(UserError):
            measurement.write({"value": 120})
        with self.assertRaises(UserError):
            measurement.with_context(_program_internal_correction=True).write({"value": 120})
        correction = self.env["project.program.measurement"].create({
            "goal_id": self.goal.id,
            "value": 250,
            "replaces_id": measurement.id,
            "correction_reason": "Corrected source data",
        })
        correction.action_validate()
        self.assertEqual(self.goal.progress_percent, 150)
        with self.assertRaises(UserError):
            self.goal.with_context(_program_revision=True).write({"superseded": True})
        revision = self.goal.action_new_goal_revision(50, direction="decrease")
        self.assertEqual(self.goal.goal_target, 200)
        self.assertEqual(revision.goal_target, 50)
        self.assertTrue(self.goal.superseded)
        self.assertFalse(revision.has_measurement)

    def test_review_publication_and_membership_revocation(self):
        participant = self.env["res.partner"].create({"name": "Participant"})
        membership = self.env["project.program.membership"].create({
            "project_id": self.project.id,
            "partner_id": participant.id,
            "role": "participant",
        })
        domain = self.env["project.program.membership"]._active_domain(participant.id)
        self.assertIn(membership, self.env["project.program.membership"].search(domain))
        review = self.env["project.program.review"].create({
            "project_id": self.project.id,
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "internal_notes": "Private",
            "public_summary": "Published result",
        })
        with self.assertRaises(UserError):
            review.with_context(_program_review_transition=True).write({"state": "published"})
        measurement = self.env["project.program.measurement"].create({
            "goal_id": self.goal.id,
            "review_id": review.id,
            "value": 125,
        })
        with self.assertRaises(UserError):
            review.action_validate()
        measurement.action_validate()
        review.action_validate()
        review.action_publish()
        self.assertEqual(review.state, "published")
        with self.assertRaises(UserError):
            review.write({"internal_notes": "Tampered"})
        membership.active = False
        self.assertFalse(self.env["project.program.membership"].search(domain))

    def test_project_copy_excludes_program_history(self):
        participant = self.env["res.partner"].create({"name": "Copy participant"})
        self.env["project.program.membership"].create({
            "project_id": self.project.id,
            "partner_id": participant.id,
            "role": "participant",
        })
        review = self.env["project.program.review"].create({
            "project_id": self.project.id,
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "public_summary": "Historical review",
        })
        measurement = self.env["project.program.measurement"].create({
            "goal_id": self.goal.id,
            "review_id": review.id,
            "value": 150,
        })
        measurement.action_validate()
        review.action_validate()
        review.action_publish()

        duplicate = self.project.copy({"name": "Copied project"})
        self.assertFalse(duplicate.program_id)
        self.assertFalse(duplicate.program_membership_ids)
        self.assertFalse(duplicate.program_review_ids)
        copied_goal = self.goal.copy({"project_id": duplicate.id})
        self.assertFalse(copied_goal.is_program_goal)
        self.assertFalse(copied_goal.measurement_ids)

    def test_session_completion_uses_done_not_cancelled(self):
        completed = self.env["project.task"].create({
            "name": "Completed session",
            "project_id": self.project.id,
            "program_activity_type": "session",
            "state": "1_done",
        })
        cancelled = self.env["project.task"].create({
            "name": "Cancelled session",
            "project_id": self.project.id,
            "program_activity_type": "session",
            "state": "1_canceled",
        })
        self.assertTrue(completed.program_session_completed)
        self.assertFalse(cancelled.program_session_completed)


@tagged("post_install", "-at_install")
class TestProjectProgramPortal(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids = [(4, cls.env.ref("project_program.group_program_manager").id)]
        cls.participant_a = new_test_user(cls.env, login="program-a@example.invalid", groups="base.group_portal")
        cls.participant_b = new_test_user(cls.env, login="program-b@example.invalid", groups="base.group_portal")
        cls.program = cls.env["project.program"].create({"name": "Portal program"})
        cls.project_a = cls.env["project.project"].create({
            "name": "Project A private", "program_id": cls.program.id,
            "company_id": cls.program.company_id.id,
        })
        cls.project_b = cls.env["project.project"].create({
            "name": "Project B private", "program_id": cls.program.id,
            "company_id": cls.program.company_id.id,
        })
        cls.project_c = cls.env["project.project"].create({
            "name": "Project C private", "program_id": cls.program.id,
            "company_id": cls.program.company_id.id,
        })
        cls.task_a = cls.env["project.task"].create({
            "name": "Project A task", "project_id": cls.project_a.id,
        })
        cls.membership_a = cls.env["project.program.membership"].create({
            "project_id": cls.project_a.id, "partner_id": cls.participant_a.partner_id.id,
            "role": "participant",
        })
        cls.env["project.program.membership"].create({
            "project_id": cls.project_b.id, "partner_id": cls.participant_a.partner_id.id,
            "role": "advisor",
        })
        cls.env["project.program.membership"].create({
            "project_id": cls.project_c.id, "partner_id": cls.participant_b.partner_id.id,
            "role": "participant",
        })
        goal = cls.env["project.milestone"].create({
            "name": "Goal A", "project_id": cls.project_a.id, "is_program_goal": True,
            "goal_unit": "points", "goal_baseline": 0, "goal_target": 10,
            "goal_direction": "increase",
        })
        review = cls.env["project.program.review"].create({
            "project_id": cls.project_a.id, "period_start": "2026-01-01",
            "period_end": "2026-01-31", "public_summary": "Public A only",
            "internal_notes": "Secret internal note",
        })
        measurement = cls.env["project.program.measurement"].create({
            "goal_id": goal.id, "review_id": review.id, "value": 0,
            "evidence_note": "Secret evidence",
        })
        measurement.action_validate()
        review.action_validate()
        review.action_publish()

    def test_portal_membership_isolation_and_revocation(self):
        self.authenticate(self.participant_a.login, self.participant_a.login)
        listing = self.url_open("/my/program-projects")
        self.assertEqual(listing.status_code, 200)
        self.assertIn("Project A private", listing.text)
        self.assertIn("Project B private", listing.text)
        self.assertNotIn("Project C private", listing.text)
        detail = self.url_open(f"/my/program-projects/{self.project_a.id}")
        self.assertEqual(detail.status_code, 200)
        self.assertIn("Public A only", detail.text)
        self.assertNotIn("Secret internal note", detail.text)
        self.assertNotIn("Secret evidence", detail.text)
        self.assertEqual(self.url_open(f"/my/program-projects/{self.project_b.id}").status_code, 200)
        self.assertEqual(self.url_open(f"/my/program-projects/{self.project_c.id}").status_code, 404)
        standard = self.url_open(f"/my/projects/{self.project_a.id}", allow_redirects=False)
        self.assertEqual(standard.status_code, 303)
        self.assertEqual(standard.headers["Location"], "/my")
        token_project = self.url_open(
            f"/my/projects/{self.project_a.id}?access_token={self.project_a.access_token}",
            allow_redirects=False,
        )
        self.assertEqual(token_project.status_code, 303)
        token_task = self.url_open(
            f"/my/projects/{self.project_a.id}/task/{self.task_a.id}?access_token={self.project_a.access_token}",
            allow_redirects=False,
        )
        self.assertEqual(token_task.status_code, 303)
        self.assertEqual(self.url_open(f"/my/projects/{self.project_a.id}/project_sharing").status_code, 403)
        self.membership_a.active = False
        self.assertEqual(self.url_open(f"/my/program-projects/{self.project_a.id}").status_code, 404)
        self.assertNotIn("Project A private", self.url_open("/my/program-projects").text)