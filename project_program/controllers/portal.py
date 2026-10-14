from odoo import _, http, fields
from odoo.addons.project.controllers.portal import ProjectCustomerPortal
from odoo.exceptions import AccessError
from odoo.http import request


class ProgramPortal(ProjectCustomerPortal):
    def _document_check_access(self, model_name, document_id, access_token=None):
        if model_name in ("project.project", "project.task"):
            document = request.env[model_name].sudo().browse(document_id).exists()
            project = document if model_name == "project.project" else document.project_id
            if project.program_id and not request.env.user._is_internal():
                raise AccessError(_("Use the authorized Program portal for this project."))
        return super()._document_check_access(model_name, document_id, access_token)

    @http.route("/my/program-projects", type="http", auth="user", website=True)
    def program_project_list(self, **kw):
        Membership = request.env["project.program.membership"].sudo()
        domain = Membership._active_domain(request.env.user.partner_id.id)
        memberships = Membership.search(domain)
        companies = request.env.user.company_ids.ids
        projects = memberships.mapped("project_id").filtered(
            lambda project: project.program_id and project.company_id.id in companies
        )
        items = [{"id": p.id, "name": p.name, "program": p.program_id.name} for p in projects]
        return request.render("project_program.portal_program_projects", {"items": items})

    @http.route("/my/program-projects/<int:project_id>", type="http", auth="user", website=True)
    def program_project_detail(self, project_id, **kw):
        Membership = request.env["project.program.membership"].sudo()
        domain = Membership._active_domain(request.env.user.partner_id.id) + [("project_id", "=", project_id)]
        membership = Membership.search(domain, limit=1)
        if not membership or not membership.project_id.program_id:
            return request.not_found()
        project = membership.project_id
        if project.company_id.id not in request.env.user.company_ids.ids:
            return request.not_found()
        reviews = request.env["project.program.review"].sudo().search([
            ("project_id", "=", project_id), ("state", "=", "published")
        ], order="period_end desc, id desc")
        published = []
        for review in reviews:
            values = []
            for measurement in review.measurement_ids.filtered(lambda m: m.state == "validated"):
                goal = measurement.goal_id
                denominator = goal.goal_target - goal.goal_baseline
                values.append({
                    "name": goal.name,
                    "unit": goal.goal_unit,
                    "baseline": goal.goal_baseline,
                    "target": goal.goal_target,
                    "value": measurement.value,
                    "progress": ((measurement.value - goal.goal_baseline) / denominator * 100.0) if denominator else False,
                })
            published.append({"period_start": review.period_start, "period_end": review.period_end,
                              "summary": review.public_summary, "values": values})
        return request.render("project_program.portal_program_project_detail", {
            "project_name": project.name, "reviews": published,
        })
