from odoo import fields, models


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
            from odoo.exceptions import AccessError
            from odoo import _
            raise AccessError(_("Only internal users can modify program configuration."))
        return super().write(vals)
