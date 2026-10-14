from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError, UserError


_REVISION_TOKEN = object()
GOAL_FIELDS = {"name", "project_id", "is_program_goal", "goal_description", "goal_unit", "goal_baseline", "goal_target", "goal_direction", "goal_revision_of_id"}


class ProjectMilestone(models.Model):
    _inherit = "project.milestone"

    is_program_goal = fields.Boolean(default=False, copy=False, index=True)
    goal_description = fields.Text(copy=False)
    goal_unit = fields.Char(copy=False)
    goal_baseline = fields.Float(copy=False)
    goal_target = fields.Float(copy=False)
    goal_direction = fields.Selection([("increase", "Increase"), ("decrease", "Decrease")], copy=False)
    goal_revision_of_id = fields.Many2one("project.milestone", copy=False, ondelete="restrict")
    superseded = fields.Boolean(default=False, copy=False, index=True)
    measurement_ids = fields.One2many("project.program.measurement", "goal_id", copy=False)
    current_value = fields.Float(compute="_compute_progress")
    has_measurement = fields.Boolean(compute="_compute_progress")
    progress_percent = fields.Float(compute="_compute_progress")

    @api.constrains("is_program_goal", "project_id", "goal_unit", "goal_baseline", "goal_target", "goal_direction", "goal_revision_of_id")
    def _check_goal(self):
        for goal in self.filtered("is_program_goal"):
            if not goal.project_id.program_id:
                raise ValidationError(_("A program goal requires a program project."))
            if not goal.goal_unit or not goal.goal_direction:
                raise ValidationError(_("A numeric goal requires a unit and direction."))
            if goal.goal_baseline == goal.goal_target:
                raise ValidationError(_("Baseline and target must be different."))
            if goal.goal_direction == "increase" and goal.goal_target < goal.goal_baseline:
                raise ValidationError(_("An increase goal needs a target above baseline."))
            if goal.goal_direction == "decrease" and goal.goal_target > goal.goal_baseline:
                raise ValidationError(_("A decrease goal needs a target below baseline."))
            if goal.goal_revision_of_id and goal.goal_revision_of_id.project_id != goal.project_id:
                raise ValidationError(_("Goal revisions must remain in one project."))

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get("is_program_goal") for vals in vals_list) and not self.env.user.has_group("project_program.group_program_user"):
            raise AccessError(_("Program goal management requires the Program User group."))
        return super().create(vals_list)

    def write(self, vals):
        if "superseded" in vals and self.env.context.get("_program_revision") is not _REVISION_TOKEN:
            raise UserError(_("Goal versions can only be superseded by creating a revision."))
        if GOAL_FIELDS.intersection(vals) and self.filtered("is_program_goal"):
            if not self.env.user.has_group("project_program.group_program_user"):
                raise AccessError(_("Program goal management requires the Program User group."))
            if any(goal.measurement_ids.filtered(lambda m: m.state == "validated") for goal in self.filtered("is_program_goal")):
                raise UserError(_("A validated goal version is immutable. Create a revision instead."))
        return super().write(vals)

    def action_new_goal_revision(self, target, unit=None, direction=None):
        self.ensure_one()
        if not self.is_program_goal or self.superseded:
            raise UserError(_("Only a current program goal can be revised."))
        if not self.env.user.has_group("project_program.group_program_user"):
            raise AccessError(_("Program goal management requires the Program User group."))
        values = {
            "name": self.name,
            "project_id": self.project_id.id,
            "is_program_goal": True,
            "goal_description": self.goal_description,
            "goal_unit": unit if unit is not None else self.goal_unit,
            "goal_baseline": self.goal_baseline,
            "goal_target": target,
            "goal_direction": direction or self.goal_direction,
            "goal_revision_of_id": self.id,
        }
        next_version = self.create(values)
        self.with_context(_program_revision=_REVISION_TOKEN).write({"superseded": True})
        return next_version

    @api.depends("goal_baseline", "goal_target", "measurement_ids.state", "measurement_ids.value", "measurement_ids.measured_at", "measurement_ids.replaced_by_id", "superseded")
    def _compute_progress(self):
        for goal in self:
            valid = goal.measurement_ids.filtered(lambda m: m.state == "validated" and not m.replaced_by_id)
            latest = valid.sorted(key=lambda m: (m.measured_at, m.id))[-1:] if valid else valid
            goal.has_measurement = bool(latest)
            goal.current_value = latest.value if latest else 0.0
            denominator = goal.goal_target - goal.goal_baseline
            goal.progress_percent = ((latest.value - goal.goal_baseline) / denominator * 100.0) if latest and denominator else 0.0

    def copy(self, default=None):
        values = dict(default or {})
        values.update({"is_program_goal": False, "goal_revision_of_id": False, "superseded": False})
        return super().copy(values)
