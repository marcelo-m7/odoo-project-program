from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError, UserError


_TRANSITION_TOKEN = object()


class ProjectProgramReview(models.Model):
    _name = "project.program.review"
    _description = "Project Program Review"
    _order = "period_end desc, id desc"

    project_id = fields.Many2one("project.project", required=True, index=True, ondelete="restrict", domain="[('program_id', '!=', False)]")
    company_id = fields.Many2one(related="project_id.company_id", store=True, index=True)
    period_start = fields.Date(required=True)
    period_end = fields.Date(required=True)
    state = fields.Selection([("draft", "Draft"), ("validated", "Validated"), ("published", "Published")], required=True, default="draft")
    internal_notes = fields.Text()
    public_summary = fields.Text()
    measurement_ids = fields.One2many("project.program.measurement", "review_id")
    validated_by = fields.Many2one("res.users", readonly=True)
    validated_at = fields.Datetime(readonly=True)
    published_by = fields.Many2one("res.users", readonly=True)
    published_at = fields.Datetime(readonly=True)
    revision_of_id = fields.Many2one("project.program.review", ondelete="restrict")

    @api.constrains("period_start", "period_end", "project_id", "measurement_ids", "revision_of_id")
    def _check_review(self):
        for rec in self:
            if rec.period_end < rec.period_start:
                raise ValidationError(_("Review end date cannot precede start date."))
            if not rec.project_id.program_id:
                raise ValidationError(_("A review requires a program project."))
            if any(m.project_id != rec.project_id for m in rec.measurement_ids):
                raise ValidationError(_("Review measurements must belong to the same project."))
            if rec.revision_of_id and rec.revision_of_id.project_id != rec.project_id:
                raise ValidationError(_("Review revisions must remain in one project."))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group("project_program.group_program_user"):
            raise AccessError(_("Program review management requires the Program User group."))
        if any(vals.get("state", "draft") != "draft" for vals in vals_list):
            raise UserError(_("Create reviews in draft."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.user.has_group("project_program.group_program_user"):
            raise AccessError(_("Program review management requires the Program User group."))
        if any(rec.state != "draft" for rec in self) and self.env.context.get("_program_review_transition") is not _TRANSITION_TOKEN:
            raise UserError(_("Validated reviews are immutable; create a revised review."))
        if "state" in vals and self.env.context.get("_program_review_transition") is not _TRANSITION_TOKEN:
            raise UserError(_("Use the review actions."))
        return super().write(vals)

    def unlink(self):
        if any(rec.state != "draft" for rec in self):
            raise UserError(_("Validated reviews cannot be deleted."))
        return super().unlink()

    def action_validate(self):
        for rec in self:
            if rec.state != "draft" or any(m.state != "validated" for m in rec.measurement_ids):
                raise UserError(_("Only draft reviews with validated measurements can be validated."))
            rec.with_context(_program_review_transition=_TRANSITION_TOKEN).write({"state": "validated", "validated_by": self.env.uid, "validated_at": fields.Datetime.now()})

    def action_publish(self):
        for rec in self:
            if rec.state != "validated" or not rec.public_summary:
                raise UserError(_("A validated review needs a public summary before publication."))
            rec.with_context(_program_review_transition=_TRANSITION_TOKEN).write({"state": "published", "published_by": self.env.uid, "published_at": fields.Datetime.now()})
