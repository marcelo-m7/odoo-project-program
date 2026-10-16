{
    "name": "Project Program",
    "summary": "Program capabilities on standard Odoo projects",
    "version": "19.0.2.0.0",
    "license": "LGPL-3",
    "category": "Services/Project",
    "depends": ["project", "portal"],
    "author": "Corvanis",
    "application": True,
    "installable": True,
    "data": [
        "views/project_views.xml",
        "views/task_views.xml",
        "views/portal_views.xml",
    ],
}
