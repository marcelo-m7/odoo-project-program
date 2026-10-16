from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProgramCore(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mentor = cls.env["res.partner"].create({"name": "Program Mentor"})
        cls.mentee = cls.env["res.partner"].create({"name": "Program Mentee"})
        cls.program = cls.env["project.project"].create({
            "name": "Mentorship Cohort",
            "is_program": True,
            "program_mentor_id": cls.mentor.id,
            "program_mentee_id": cls.mentee.id,
        })
        cls.standard = cls.env["project.project"].create({"name": "Regular Project"})
        cls.task_a = cls.env["project.task"].create({
            "name": "Discovery",
            "project_id": cls.program.id,
            "program_objective": "First objective",
            "program_followup": "First follow-up",
        })
        cls.task_b = cls.env["project.task"].create({
            "name": "Review",
            "project_id": cls.program.id,
            "program_objective": "Second objective",
        })

    def test_flag_is_per_project(self):
        self.assertTrue(self.program.is_program)
        self.assertFalse(self.standard.is_program)
        self.assertTrue(self.task_a.is_program)
        self.assertFalse(self.env["project.task"].create({
            "name": "Ordinary Task", "project_id": self.standard.id,
        }).is_program)

    def test_contacts_belong_to_project(self):
        self.assertEqual(self.program.program_mentor_id, self.mentor)
        self.assertEqual(self.program.program_mentee_id, self.mentee)
        self.assertFalse(self.standard.program_mentor_id)

    def test_task_notes_are_independent_and_persisted(self):
        self.task_a.write({"program_objective": "Updated in backend"})
        self.assertEqual(self.task_a.read(["program_objective"])[0]["program_objective"], "Updated in backend")
        self.assertEqual(self.task_b.program_objective, "Second objective")

    def test_portal_cannot_write_program_configuration_or_notes(self):
        portal_group = self.env.ref("base.group_portal")
        portal = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Project Portal Tester",
            "login": "program.portal.test@example.invalid",
            "email": "program.portal.test@example.invalid",
            "group_ids": [(6, 0, [portal_group.id])],
        })
        with self.assertRaises(AccessError):
            self.program.with_user(portal).write({"program_mentor_id": self.mentee.id})
        with self.assertRaises(AccessError):
            self.task_a.with_user(portal).write({"program_followup": "Forged RPC"})
        with self.assertRaises(AccessError):
            self.env["project.task"].with_user(portal).create({
                "name": "Forged", "project_id": self.program.id,
                "program_objective": "Forged",
            })

    def test_portal_cannot_inject_program_fields_on_project_create(self):
        portal = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Program Project Creation Probe",
            "login": "program.project.create@example.invalid",
            "group_ids": [(6, 0, [self.env.ref("base.group_portal").id])],
        })
        with self.assertRaises(AccessError):
            self.env["project.project"].with_user(portal).create({
                "name": "Unauthorised program",
                "is_program": True,
            })

    def test_program_task_flag_tracks_project_changes(self):
        self.assertTrue(self.task_a.is_program)
        self.program.write({"is_program": False})
        self.assertFalse(self.task_a.is_program)
        self.assertFalse(self.task_b.is_program)
        self.assertEqual(self.task_a.program_objective, "First objective")
        self.program.write({"is_program": True})
        self.assertTrue(self.task_a.is_program)

    def test_project_sharing_uses_same_persisted_fields(self):
        form = self.env.ref("project_program.view_task_sharing_program")
        self.assertEqual(form.model, "project.task")
        self.assertEqual(
            form.inherit_id,
            self.env.ref("project.project_sharing_project_task_view_form"),
        )
        self.assertIn("program_objective", form.arch_db)
        self.assertIn("program_followup", form.arch_db)
        self.assertIn('invisible="not is_program"', form.arch_db)
