from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError, UserError


_VALIDATE_TOKEN = object()
_CORRECTION_TOKEN = object()


class ProjectProgramMeasurement(models.Model):
    _name = "project.program.measurement"
    _description = "Program Goal Measurement"
    _order = "measured_at desc, id desc"

    goal_id = fields.Many2one("project.milestone", required=True, index=True, ondelete="restrict", domain="[('is_program_goal', '=', True)]")
    project_id = fields.Many2one(related="goal_id.project_id", store=True, index=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True, index=True)
    measured_at = fields.Date(required=True, default=fields.Date.context_today)
    value = fields.Float(required=True)
    evidence_note = fields.Text()
    evidence_attachment_ids = fields.Many2many("ir.attachment", string="Internal evidence")
    state = fields.Selection([("draft", "Draft"), ("validated", "Validated")], required=True, default="draft")
    validated_by = fields.Many2one("res.users", readonly=True)
    validated_at = fields.Datetime(readonly=True)
    review_id = fields.Many2one("project.program.review", index=True, ondelete="restrict")
    replaces_id = fields.Many2one("project.program.measurement", ondelete="restrict")
    replaced_by_id = fields.Many2one("project.program.measurement", ondelete="restrict", readonly=True)
    correction_reason = fields.Text()

    @api.constrains("goal_id", "review_id", "replaces_id", "correction_reason")
    def _check_links(self):
        for rec in self:
            if not rec.goal_id.is_program_goal:
                raise ValidationError(_("Measurements require a program goal."))
            if rec.review_id and rec.review_id.project_id != rec.project_id:
                raise ValidationError(_("Review and measurement must belong to one project."))
            if rec.replaces_id:
                if rec.replaces_id.goal_id != rec.goal_id or rec.replaces_id.state != "validated" or not rec.correction_reason:
                    raise ValidationError(_("A correction needs a reason and a validated measurement of the same goal."))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group("project_program.group_program_user"):
            raise AccessError(_("Program measurement management requires the Program User group."))
        if any(vals.get("state", "draft") != "draft" for vals in vals_list):
            raise UserError(_("Create measurements in draft, then validate them."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.user.has_group("project_program.group_program_user"):
            raise AccessError(_("Program measurement management requires the Program User group."))
        if any(rec.state == "validated" for rec in self) and self.env.context.get("_program_internal_correction") is not _CORRECTION_TOKEN:
            raise UserError(_("Validated measurements cannot be changed; create a correction."))
        if "state" in vals and vals["state"] == "validated" and self.env.context.get("_program_validate_measurement") is not _VALIDATE_TOKEN:
            raise UserError(_("Use the validation action."))
        return super().write(vals)

    def unlink(self):
        if any(rec.state == "validated" for rec in self):
            raise UserError(_("Validated measurements cannot be deleted."))
        return super().unlink()

    def action_validate(self):
        for rec in self:
            if rec.state != "draft" or rec.goal_id.superseded:
                raise UserError(_("Only draft measurements of current goal versions can be validated."))
            if rec.replaces_id and rec.replaces_id.replaced_by_id:
                raise UserError(_("The source measurement was already corrected."))
            rec.with_context(_program_validate_measurement=_VALIDATE_TOKEN).write({"state": "validated", "validated_by": self.env.uid, "validated_at": fields.Datetime.now()})
            if rec.replaces_id:
                rec.replaces_id.with_context(_program_internal_correction=_CORRECTION_TOKEN).write({"replaced_by_id": rec.id})
