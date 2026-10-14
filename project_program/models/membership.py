from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectProgramMembership(models.Model):
    _name = "project.program.membership"
    _description = "Project Program Membership"
    _order = "project_id, role, partner_id"

    project_id = fields.Many2one("project.project", required=True, index=True, ondelete="cascade", domain="[('program_id', '!=', False)]")
    program_id = fields.Many2one(related="project_id.program_id", store=True, index=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True, index=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    role = fields.Selection([("participant", "Participant"), ("advisor", "Advisor")], required=True)
    is_lead = fields.Boolean(string="Lead advisor")
    valid_from = fields.Date(required=True, default=fields.Date.context_today)
    valid_to = fields.Date()
    active = fields.Boolean(default=True)

    @api.constrains("project_id", "partner_id", "role", "is_lead", "valid_from", "valid_to", "active")
    def _check_membership(self):
        Membership = self.with_context(active_test=False)
        for rec in self:
            if not rec.project_id.program_id:
                raise ValidationError(_("Membership requires a program project."))
            if rec.partner_id.is_company:
                raise ValidationError(_("Membership requires an individual contact."))
            if rec.valid_to and rec.valid_to < rec.valid_from:
                raise ValidationError(_("Membership end date cannot precede start date."))
            if rec.is_lead and rec.role != "advisor":
                raise ValidationError(_("Only an advisor can be lead."))
            if not rec.active:
                continue
            peers = Membership.search([("id", "!=", rec.id), ("project_id", "=", rec.project_id.id), ("active", "=", True)])
            for peer in peers:
                overlap = (not rec.valid_to or peer.valid_from <= rec.valid_to) and (not peer.valid_to or rec.valid_from <= peer.valid_to)
                if not overlap:
                    continue
                if rec.partner_id == peer.partner_id and rec.role == peer.role:
                    raise ValidationError(_("Duplicate active membership dates are not allowed."))
                if rec.is_lead and peer.is_lead:
                    raise ValidationError(_("Only one lead advisor may be active in a project at a time."))

    @api.model
    def _active_domain(self, partner_id, on_date=None):
        today = on_date or fields.Date.context_today(self)
        return [("partner_id", "=", partner_id), ("active", "=", True), ("valid_from", "<=", today), "|", ("valid_to", "=", False), ("valid_to", ">=", today)]
