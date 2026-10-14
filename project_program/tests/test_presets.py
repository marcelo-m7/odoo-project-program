from odoo.tests import tagged
from .common import ProgramCase


@tagged('post_install', '-at_install')
class TestProgramPresets(ProgramCase):
    def test_ae_and_facodi_presets(self):
        for profile in ('ae', 'facodi'):
            wizard = self.env['project.program.setup'].create({
                'name': f'{profile} pilot', 'profile': profile,
                'date_start': '2026-01-01', 'date_end': '2026-06-30'})
            action = wizard.action_create_program()
            program = self.env['project.program'].browse(action['res_id'])
            self.assertEqual(len(program.project_ids), 1)
            project = program.project_ids
            self.assertEqual(len(project.program_goal_ids), 3)
            self.assertTrue(project.task_ids)
            self.assertFalse(project.program_membership_ids)
            self.assertFalse(project.program_review_ids)
