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

Before any production update, take a coherent PostgreSQL and filestore backup, rehearse the update on staging and retain the prior source revision. Rollback restores both database and filestore together; module uninstall is not a rollback strategy.
