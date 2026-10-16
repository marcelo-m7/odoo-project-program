from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class ProjectProject(models.Model):
    _inherit = "project.project"

    is_program = fields.Boolean(
        string="Is a Program",
        default=False,
        index=True,
        copy=False,
        help="Enable program-specific views without replacing the standard Project app.",
    )
    program_mentor_id = fields.Many2one(
        "res.partner",
        string="Mentor",
        copy=False,
        tracking=True,
        help="Contact acting as the mentor for this project.",
    )
    program_mentee_id = fields.Many2one(
        "res.partner",
        string="Mentorando",
        copy=False,
        tracking=True,
        help="Contact participating as the mentee in this program.",
    )

    def write(self, vals):
        # Field-level readonly attributes in XML are not an RPC authorization boundary.
        if not self.env.user._is_internal() and set(vals) & {
            "is_program", "program_mentor_id", "program_mentee_id",
        }:
            raise AccessError(_("Only internal users can modify program configuration."))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        protected = {"is_program", "program_mentor_id", "program_mentee_id"}
        if not self.env.user._is_internal() and any(protected & vals.keys() for vals in vals_list):
            raise AccessError(_("Only internal users can configure program projects."))
        return super().create(vals_list)
