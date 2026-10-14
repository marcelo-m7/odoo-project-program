from odoo import fields
from odoo.tests.common import TransactionCase, new_test_user


class ProgramCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(cls.env, login='program_manager',
            groups='project_program.group_program_manager')
        cls.coordinator = new_test_user(cls.env, login='program_owner',
            groups='project_program.group_program_user')
        cls.outsider = new_test_user(cls.env, login='program_outsider',
            groups='project_program.group_program_user')
        cls.program = cls.env['project.program'].create({
            'name': 'Program A', 'user_id': cls.coordinator.id,
            'date_start': '2026-01-01', 'date_end': '2026-12-31'})
        cls.project = cls.env['project.project'].create({
            'name': 'Project A', 'program_id': cls.program.id,
            'user_id': cls.coordinator.id, 'company_id': cls.env.company.id})
        cls.goal = cls.env['project.program.goal'].create({
            'name': 'Published goal', 'project_id': cls.project.id,
            'baseline': 10, 'target': 20, 'unit': 'units'})

    def measure(self, value=15, **kwargs):
        return self.env['project.program.measurement'].create({
            'goal_id': self.goal.id, 'value': value,
            'measured_at': '2026-06-15', **kwargs})

    def review(self, **kwargs):
        return self.env['project.program.review'].create({
            'project_id': self.project.id, 'period_start': '2026-06-01',
            'period_end': '2026-06-30', 'public_summary': 'Public progress',
            'internal_notes': 'SECRET INTERNAL NOTE', **kwargs})
