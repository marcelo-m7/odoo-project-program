from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = "project.project"

    program_id = fields.Many2one("project.program", index=True, copy=False, ondelete="restrict")
    program_membership_ids = fields.One2many("project.program.membership", "project_id", copy=False)
    program_review_ids = fields.One2many("project.program.review", "project_id", copy=False)

    @api.constrains("program_id", "company_id")
    def _check_program_company(self):
        for project in self:
            if project.program_id and project.company_id != project.program_id.company_id:
                raise ValidationError(_("The project and program must belong to the same company."))
