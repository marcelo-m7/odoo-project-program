from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    program_activity_type = fields.Selection([
        ("action", "Action"), ("session", "Session"), ("workshop", "Workshop"), ("review", "Review"),
    ], default="action", index=True)
    calendar_event_id = fields.Many2one("calendar.event", copy=False)
    program_session_outcome = fields.Text(copy=False, groups="project_program.group_program_user")
    program_id = fields.Many2one(related="project_id.program_id", store=True, index=True)
    program_session_completed = fields.Boolean(compute="_compute_program_session_completed", store=True)

    @api.depends("program_activity_type", "state")
    def _compute_program_session_completed(self):
        for task in self:
            task.program_session_completed = task.program_activity_type == "session" and task.state == "1_done"
