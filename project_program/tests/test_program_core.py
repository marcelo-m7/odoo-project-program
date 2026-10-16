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
            "groups_id": [(6, 0, [portal_group.id])],
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
