from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProgramContract(TransactionCase):
    def test_program_models_registered(self):
        for model in ('project.program', 'project.program.membership',
                      'project.program.goal', 'project.program.measurement',
                      'project.program.review'):
            self.assertIn(model, self.env.registry.models)

    def test_application(self):
        module = self.env['ir.module.module'].search([('name', '=', 'project_program')])
        self.assertTrue(module.application)
