from datetime import timedelta
from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import HttpCase, new_test_user, tagged
from .common import ProgramCase


@tagged('post_install', '-at_install')
class TestProgramPortal(ProgramCase, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = new_test_user(cls.env, login='program_portal', groups='base.group_portal')
        cls.other_portal = new_test_user(cls.env, login='program_portal_other', groups='base.group_portal')
        cls.member = cls.env['project.program.membership'].create({
            'project_id': cls.project.id, 'partner_id': cls.portal_user.partner_id.id})

    def publish(self):
        r = self.review()
        self.measure(review_id=r.id)
        r.action_validate()
        r.action_publish()
        return r

    def test_published_projection_and_revocation(self):
        r = self.publish()
        self.measure(987654)
        self.authenticate(self.portal_user.login, self.portal_user.login)
        page = self.url_open(f'/my/programs/{self.project.id}')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Public progress', page.text)
        self.assertIn('Published goal', page.text)
        self.assertNotIn('SECRET INTERNAL NOTE', page.text)
        self.assertNotIn('987654', page.text)
        r.action_unpublish()
        self.assertNotIn('Public progress', self.url_open(f'/my/programs/{self.project.id}').text)
        self.member.active = False
        self.assertEqual(self.url_open(f'/my/programs/{self.project.id}').status_code, 404)

    def test_other_person_and_commercial_partner_not_authorized(self):
        self.publish()
        company = self.env['res.partner'].create({'name': 'Shared company', 'is_company': True})
        (self.portal_user.partner_id | self.other_portal.partner_id).parent_id = company
        self.authenticate(self.other_portal.login, self.other_portal.login)
        self.assertEqual(self.url_open(f'/my/programs/{self.project.id}').status_code, 404)
        self.assertNotIn('Project A', self.url_open('/my/programs').text)

    def test_expired_member_is_denied_immediately(self):
        self.publish()
        self.member.write({'valid_from': fields.Date.today()-timedelta(days=5),
                           'valid_to': fields.Date.today()-timedelta(days=1)})
        self.authenticate(self.portal_user.login, self.portal_user.login)
        self.assertEqual(self.url_open(f'/my/programs/{self.project.id}').status_code, 404)

    def test_native_project_token_cannot_bypass(self):
        self.project._portal_ensure_token()
        self.authenticate(self.other_portal.login, self.other_portal.login)
        page = self.url_open(f'/my/projects/{self.project.id}?access_token={self.project.access_token}', allow_redirects=False)
        self.assertIn(page.status_code, (302, 303, 403, 404))
        self.assertNotIn('Project A', page.text)

    def test_portal_rpc_cannot_read_raw_records(self):
        self.publish()
        for record in (self.goal, self.program, self.review()):
            with self.assertRaises(AccessError):
                record.with_user(self.portal_user).read()

    def test_archived_program_and_project_deny(self):
        self.authenticate(self.portal_user.login, self.portal_user.login)
        self.project.active = False
        self.assertEqual(self.url_open(f'/my/programs/{self.project.id}').status_code, 404)
        self.project.active = True
        self.program.active = False
        self.assertEqual(self.url_open(f'/my/programs/{self.project.id}').status_code, 404)
