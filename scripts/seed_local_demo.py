import json
import os
import secrets
from pathlib import Path

DATABASE_NAME = env.cr.dbname
if DATABASE_NAME != "project_program_local":
    raise RuntimeError(f"Refusing to seed non-demo database: {DATABASE_NAME}")

project_root = Path.cwd()
local_dir = project_root / ".local"
local_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
accounts_path = local_dir / "demo_accounts.json"
try:
    accounts = json.loads(accounts_path.read_text())
except FileNotFoundError:
    accounts = {}


def password_for(key):
    if key not in accounts:
        accounts[key] = secrets.token_urlsafe(24)
    return accounts[key]


def ensure_user(login, display_name, group_xmlids, account_key):
    user = env["res.users"].with_context(no_reset_password=True).search([("login", "=", login)], limit=1)
    values = {
        "name": display_name,
        "login": login,
        "email": login,
        "password": password_for(account_key),
        "company_id": env.company.id,
        "company_ids": [(6, 0, [env.company.id])],
        "group_ids": [(6, 0, [env.ref(xmlid).id for xmlid in group_xmlids])],
    }
    if user:
        user.write(values)
    else:
        user = env["res.users"].with_context(no_reset_password=True).create(values)
    return user


manager = ensure_user(
    "demo.program.manager@example.invalid",
    "Demo Program Manager",
    ["base.group_user", "project_program.group_program_manager"],
    "manager_password",
)
participant = ensure_user(
    "demo.program.participant@example.invalid",
    "Demo Program Participant",
    ["base.group_portal"],
    "participant_password",
)
env = env(user=manager, su=False)

Program = env["project.program"]
program = Program.search([("code", "=", "LOCAL-2026")], limit=1)
if not program:
    program = Program.create({
        "name": "Programa de Demonstração 2026",
        "code": "LOCAL-2026",
        "company_id": env.company.id,
        "user_id": manager.id,
        "date_start": "2026-01-01",
        "date_end": "2026-12-31",
    })
if program.state == "draft":
    program.action_activate()

Project = env["project.project"].sudo()
project = Project.search([("program_id", "=", program.id), ("name", "=", "Iniciativa de Inclusão Produtiva")], limit=1)
if not project:
    project = Project.create({
        "name": "Iniciativa de Inclusão Produtiva",
        "program_id": program.id,
        "company_id": program.company_id.id,
        "user_id": manager.id,
    })

Membership = env["project.program.membership"]
membership = Membership.search([
    ("project_id", "=", project.id),
    ("partner_id", "=", participant.partner_id.id),
    ("role", "=", "participant"),
], limit=1)
if not membership:
    Membership.create({
        "project_id": project.id,
        "partner_id": participant.partner_id.id,
        "role": "participant",
    })

Goal = env["project.milestone"]
goal_specs = [
    ("Empresas acompanhadas", "empresas", 0, 20, "increase", 24),
    ("Empregos criados", "empregos", 10, 25, "increase", 0),
    ("Investimento mobilizado", "EUR", 50000, 100000, "increase", None),
]
goals = []
for name, unit, baseline, target, direction, observed in goal_specs:
    goal = Goal.search([("project_id", "=", project.id), ("name", "=", name), ("is_program_goal", "=", True)], limit=1)
    if not goal:
        goal = Goal.create({
            "name": name,
            "project_id": project.id,
            "is_program_goal": True,
            "goal_description": f"Indicador de demonstração: {name.lower()}.",
            "goal_unit": unit,
            "goal_baseline": baseline,
            "goal_target": target,
            "goal_direction": direction,
        })
    goals.append((goal, observed))

Review = env["project.program.review"]
review = Review.search([("project_id", "=", project.id), ("period_start", "=", "2026-01-01"), ("period_end", "=", "2026-03-31")], limit=1)
if not review:
    review = Review.create({
        "project_id": project.id,
        "period_start": "2026-01-01",
        "period_end": "2026-03-31",
        "public_summary": "Acompanhamento trimestral: duas metas apresentam resultados observados; o investimento mobilizado aguarda confirmação documental.",
        "internal_notes": "Dado fictício para demonstração local. Validar comprovativos antes de uma publicação real.",
    })

Measurement = env["project.program.measurement"]
for goal, observed in goals:
    if observed is None:
        continue
    measurement = Measurement.search([("goal_id", "=", goal.id), ("review_id", "=", review.id)], limit=1)
    if not measurement:
        measurement = Measurement.create({
            "goal_id": goal.id,
            "review_id": review.id,
            "value": observed,
            "evidence_note": "Evidência fictícia, criada apenas para testes locais.",
        })
    if measurement.state == "draft":
        measurement.action_validate()
if review.state == "draft":
    review.action_validate()
if review.state == "validated":
    review.action_publish()

Task = env["project.task"]
task = Task.search([("project_id", "=", project.id), ("name", "=", "Sessão de acompanhamento trimestral")], limit=1)
if not task:
    Task.create({
        "name": "Sessão de acompanhamento trimestral",
        "project_id": project.id,
        "program_activity_type": "session",
        "state": "1_done",
        "description": "Sessão fictícia concluída para demonstração do ciclo de atividades.",
    })

accounts["manager_login"] = manager.login
accounts["participant_login"] = participant.login
accounts_path.write_text(json.dumps(accounts, indent=2) + "\n")
os.chmod(accounts_path, 0o600)
os.chmod(local_dir, 0o700)
env.cr.commit()

print(f"Seeded fictional local demo records in {DATABASE_NAME}.")
print(f"Accounts and generated credentials: {accounts_path}")
print("No passwords were printed to the terminal.")
