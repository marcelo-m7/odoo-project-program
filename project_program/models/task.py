from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class ProjectTask(models.Model):
    _inherit = "project.task"

    is_program = fields.Boolean(
        related="project_id.is_program",
        string="Program Task",
        store=True,
        readonly=True,
    )
    program_objective = fields.Text(
        string="Objetivo do Programa",
        copy=False,
    )
    program_followup = fields.Text(
        string="Acompanhamento do Programa",
        copy=False,
    )

    @property
    def TASK_PORTAL_READABLE_FIELDS(self):
        """Extend only task reads, never the portal writable allowlist."""
        return [*super().TASK_PORTAL_READABLE_FIELDS,
                "is_program", "program_objective", "program_followup"]

    def write(self, vals):
        if not self.env.user._is_internal() and {
            "program_objective", "program_followup",
        } & set(vals):
            raise AccessError(_("Program notes can only be edited by internal users."))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user._is_internal() and any(
            {"program_objective", "program_followup"} & set(vals)
            for vals in vals_list
        ):
            raise AccessError(_("Program notes can only be edited by internal users."))
        return super().create(vals_list)
