from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class ProjectProgram(models.Model):
    _name = "project.program"
    _description = "Project Program"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    user_id = fields.Many2one("res.users", string="Coordinator", tracking=True)
    date_start = fields.Date(tracking=True)
    date_end = fields.Date(tracking=True)
    state = fields.Selection([("draft", "Draft"), ("active", "Active"), ("closed", "Closed")], default="draft", required=True, tracking=True)
    active = fields.Boolean(default=True)
    project_ids = fields.One2many("project.project", "program_id", string="Projects")
    project_count = fields.Integer(compute="_compute_counts")
    goal_count = fields.Integer(compute="_compute_counts")
    pending_review_count = fields.Integer(compute="_compute_counts")

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(_("The end date cannot precede the start date."))

    @api.constrains("company_id", "project_ids")
    def _check_project_companies(self):
        for rec in self:
            if any(project.company_id != rec.company_id for project in rec.project_ids):
                raise ValidationError(_("Projects and their program must belong to the same company."))

    def action_activate(self):
        for rec in self:
            if rec.state != "draft" or not rec.user_id or not rec.date_start or not rec.date_end:
                raise UserError(_("A draft program needs a coordinator and both dates before activation."))
        self.write({"state": "active"})

    def action_close(self):
        if any(rec.state != "active" for rec in self):
            raise UserError(_("Only active programs can be closed."))
        self.write({"state": "closed"})

    def _compute_counts(self):
        Project = self.env["project.project"]
        Goal = self.env["project.milestone"]
        Review = self.env["project.program.review"]
        for rec in self:
            projects = Project.search([("program_id", "=", rec.id)])
            rec.project_count = len(projects)
            rec.goal_count = Goal.search_count([("project_id", "in", projects.ids), ("is_program_goal", "=", True), ("superseded", "=", False)])
            rec.pending_review_count = Review.search_count([("project_id", "in", projects.ids), ("state", "!=", "published")])

    def action_view_projects(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "name": _("Projects"), "res_model": "project.project", "view_mode": "list,form", "domain": [("program_id", "=", self.id)]}

    def action_view_goals(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "name": _("Goals"), "res_model": "project.milestone", "view_mode": "list,form", "domain": [("project_id.program_id", "=", self.id), ("is_program_goal", "=", True)]}

    def action_view_reviews(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "name": _("Reviews"), "res_model": "project.program.review", "view_mode": "list,form", "domain": [("project_id.program_id", "=", self.id)]}
