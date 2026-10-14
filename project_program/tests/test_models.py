from datetime import timedelta
from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from .common import ProgramCase


@tagged('post_install', '-at_install')
class TestProgramModels(ProgramCase):
    def test_lifecycle_and_dates(self):
        self.program.with_user(self.coordinator).action_activate()
        self.assertEqual(self.program.state, 'active')
        self.program.action_close()
        self.assertEqual(self.program.state, 'closed')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.program.date_end = '2025-01-01'

    def test_state_cannot_be_injected(self):
        with self.assertRaises(UserError):
            self.program.write({'state': 'active'})
        with self.assertRaises(UserError):
            self.measure(state='validated')
        with self.assertRaises(UserError):
            self.review(state='published')

    def test_decreasing_and_missing_progress(self):
        self.assertFalse(self.goal.has_measurement)
        self.goal.write({'direction': 'decrease', 'baseline': 20, 'target': 10})
        m = self.measure(5)
        m.action_validate()
        self.assertTrue(self.goal.has_measurement)
        self.assertEqual(self.goal.progress, 150)

    def test_zero_measurement_is_not_missing(self):
        self.goal.write({'baseline': -10, 'target': 10})
        self.measure(0).action_validate()
        self.assertTrue(self.goal.has_measurement)
        self.assertEqual(self.goal.progress, 50)

    def test_draft_measurement_does_not_change_progress(self):
        self.measure(999)
        self.assertFalse(self.goal.has_measurement)

    def test_frozen_measurement_and_goal(self):
        m = self.measure()
        m.action_validate()
        for changes in ({'value': 99}, {'goal_id': False}, {'state': 'draft'}):
            with self.assertRaises(UserError):
                m.with_context(allow_validated_write=True).write(changes)
        with self.assertRaises(UserError):
            m.unlink()
        with self.assertRaises(UserError):
            self.goal.target = 99
        action = self.goal.action_revision()
        revised = self.env['project.program.goal'].browse(action['res_id'])
        revised.target = 30
        self.assertEqual(revised.revision_of_id, self.goal)
        self.assertEqual(m.goal_id.target, 20)

    def test_review_freeze_publication_and_unpublish(self):
        r = self.review()
        m = self.measure(review_id=r.id)
        r.action_validate()
        self.assertEqual(m.state, 'validated')
        r.action_publish()
        self.assertEqual(r.state, 'published')
        for changes in ({'public_summary': 'changed'}, {'internal_notes': 'changed'}, {'state': 'draft'}):
            with self.assertRaises(UserError):
                r.write(changes)
        with self.assertRaises(UserError):
            m.review_id = False
        with self.assertRaises(UserError):
            self.measure(review_id=r.id)
        r.action_unpublish()
        self.assertEqual(r.state, 'validated')

    def test_review_period_and_project_integrity(self):
        r = self.review()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.measure(review_id=r.id, measured_at='2026-05-01')
        other = self.env['project.project'].create({'name': 'Other', 'program_id': self.program.id})
        r.project_id = other
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.measure(review_id=r.id)

    def test_company_integrity(self):
        other = self.env['res.company'].create({'name': 'Other organisation'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.project.company_id = other
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.program.company_id = other

    def test_program_and_project_copy_clean(self):
        member = self.env['res.partner'].create({'name': 'Member'})
        self.env['project.program.membership'].create({'project_id': self.project.id, 'partner_id': member.id})
        self.measure()
        self.review()
        new = self.program.copy()
        self.assertFalse(new.project_ids)
        p = self.project.copy()
        self.assertFalse(p.program_id)
        self.assertFalse(p.program_membership_ids)
        self.assertFalse(p.program_goal_ids)
        self.assertFalse(p.program_review_ids)

    def test_internal_record_isolation(self):
        self.assertTrue(self.program.with_user(self.coordinator).read(['name']))
        with self.assertRaises(AccessError):
            self.program.with_user(self.outsider).read(['name'])
        self.assertTrue(self.program.with_user(self.manager).read(['name']))
        with self.assertRaises(AccessError):
            self.goal.with_user(self.outsider).write({'name': 'Hijacked'})

    def test_membership_dates_and_overlap(self):
        contact = self.env['res.partner'].create({'name': 'Advisor'})
        M = self.env['project.program.membership']
        m = M.create({'project_id': self.project.id, 'partner_id': contact.id,
                      'role': 'advisor', 'is_lead': True})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            M.create({'project_id': self.project.id, 'partner_id': contact.id, 'role': 'advisor'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            m.valid_to = fields.Date.today() - timedelta(days=1)
        m.active = False
        self.assertFalse(m.is_current)

    def test_session_count_excludes_cancelled(self):
        T = self.env['project.task']
        for state in ('1_done', '1_canceled', '01_in_progress'):
            T.create({'name': state, 'project_id': self.project.id,
                      'program_activity_type': 'session', 'state': state})
        self.assertEqual(self.program.completed_session_count, 1)

    def test_goal_invalid_target(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.goal.target = 10
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.goal.target = 9

    def test_project_cannot_detach_history(self):
        self.measure().action_validate()
        with self.assertRaises(UserError):
            self.project.program_id = False
        with self.assertRaises(UserError):
            self.project.unlink()
