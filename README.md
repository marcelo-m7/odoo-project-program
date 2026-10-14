# Project Program

An Odoo 19 addon for time bounded programs built on standard Projects, Tasks, Milestones, Calendar and Portal. The generic addon contains no Algarve Evolution contacts or program records.

The [V5 specification](https://docs.google.com/document/d/1FrvqvxU-dVVokiOCZ0SSG6s34D6W7QiqN5jP9y8omA0/edit) and [commercial proposal](https://docs.google.com/document/d/17XTYM_dX44yoXK39eepwofIxyxNinmB93f2yZI50R90/edit) are design inputs. The proposal remains subject to client validation.

See [architecture](docs/architecture.md), [milestone ADR](docs/adr/0001-milestone-goals.md), [security](docs/security.md), and [acceptance matrix](docs/acceptance.md).

## Development

Use an Odoo 19 checkout and a disposable PostgreSQL database. Add this repository to `--addons-path`, install `project_program`, then run tagged addon tests. Never use a production database for tests.

```bash
python odoo-bin -d project_program_test -i project_program --addons-path=addons,/path/to/odoo-project-program --test-enable --stop-after-init --log-level=test
python odoo-bin -d project_program_test -u project_program --addons-path=addons,/path/to/odoo-project-program --test-enable --stop-after-init --log-level=test
```

### Local demo

In the supplied workspace, `../Codoo` contains the Odoo 19 checkout and Python environment. From this repository:

```bash
./scripts/local.sh setup
./scripts/local.sh run
```

Run `./scripts/local.sh test` in a separate terminal to install/upgrade and test on `project_program_test_local`. Open `http://127.0.0.1:8069` for the demo. The setup command creates or upgrades only the dedicated `project_program_local` database, installs the addon, and seeds fictional program/project/goal/review data plus an internal manager and a portal participant. The web runner binds only to localhost, filters HTTP requests to that database, and disables cron workers because this workstation's PostgreSQL contains unrelated test databases. The generated local-only logins/passwords are written with owner-only permissions to `.local/demo_accounts.json`; never copy these demo accounts into a shared or production database. The setup command refuses to seed any database other than `project_program_local` and does not drop an existing database.

Set `ODOO_ROOT`, `ODOO_PYTHON`, `ODOO_DB_USER`, `ODOO_DB_HOST`, `ODOO_HTTP_PORT`, or `ODOO_TEST_HTTP_PORT` to override the workspace defaults. The test server uses the demo port plus one by default. See [the local E2E report](docs/local-e2e-report.md) for use cases and captured evidence.

Before any production update, take a coherent PostgreSQL and filestore backup, rehearse the update on staging and retain the prior source revision. Rollback restores both database and filestore together; module uninstall is not a rollback strategy.
