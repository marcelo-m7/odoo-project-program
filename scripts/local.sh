#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ODOO_ROOT="${ODOO_ROOT:-$(cd "$PROJECT_ROOT/../Codoo" && pwd)}"
ODOO_BIN="${ODOO_BIN:-$ODOO_ROOT/odoo/odoo/odoo-bin}"
ODOO_PYTHON="${ODOO_PYTHON:-$ODOO_ROOT/.venv/bin/python}"
ODOO_DB_NAME="project_program_local"
ODOO_DB_USER="${ODOO_DB_USER:-$(id -un)}"
ODOO_DB_HOST="${ODOO_DB_HOST:-/var/run/postgresql}"
ODOO_HTTP_PORT="${ODOO_HTTP_PORT:-8069}"
ODOO_TEST_HTTP_PORT="${ODOO_TEST_HTTP_PORT:-$((ODOO_HTTP_PORT + 1))}"
ADDONS_PATH="$ODOO_ROOT/odoo/odoo/addons,$ODOO_ROOT/odoo/enterprise,$PROJECT_ROOT"

if [[ ! -x "$ODOO_PYTHON" ]]; then
    printf 'Odoo Python executable not found: %s\nSet ODOO_PYTHON to an Odoo 19 environment.\n' "$ODOO_PYTHON" >&2
    exit 1
fi
if [[ ! -f "$ODOO_BIN" ]]; then
    printf 'Odoo executable not found: %s\nSet ODOO_ROOT or ODOO_BIN to an Odoo 19 checkout.\n' "$ODOO_BIN" >&2
    exit 1
fi

odoo() {
    "$ODOO_PYTHON" "$ODOO_BIN" "$@" \
        --db_user="$ODOO_DB_USER" \
        --db_host="$ODOO_DB_HOST" \
        --addons-path="$ADDONS_PATH" \
        --http-interface=127.0.0.1 \
        --max-cron-threads=0
}

case "${1:-}" in
    setup)
        cd "$PROJECT_ROOT"
        database_exists="$(psql -h "$ODOO_DB_HOST" -U "$ODOO_DB_USER" -d postgres -Atqc \
            "SELECT 1 FROM pg_database WHERE datname = '$ODOO_DB_NAME'")"
        module_state=""
        if [[ "$database_exists" == "1" ]]; then
            module_state="$(psql -h "$ODOO_DB_HOST" -U "$ODOO_DB_USER" -d "$ODOO_DB_NAME" -Atqc \
                "SELECT state FROM ir_module_module WHERE name = 'project_program'")"
        fi
        if [[ "$module_state" == "installed" ]]; then
            module_action=(-u project_program)
            printf 'Upgrading project_program in the existing local demo database.\n'
        else
            module_action=(-i project_program)
            printf 'Installing project_program in a new local demo database.\n'
        fi
        odoo -d "$ODOO_DB_NAME" "${module_action[@]}" --stop-after-init --log-level=warn
        odoo shell -d "$ODOO_DB_NAME" < "$PROJECT_ROOT/scripts/seed_local_demo.py"
        printf 'Local demo ready. Review .local/demo_accounts.json for generated demo logins.\n'
        ;;
    run)
        exec "$ODOO_PYTHON" "$ODOO_BIN" \
            --db_user="$ODOO_DB_USER" \
            --db_host="$ODOO_DB_HOST" \
            --addons-path="$ADDONS_PATH" \
            --db-filter="^${ODOO_DB_NAME}$" \
            --max-cron-threads=0 \
            --http-interface=127.0.0.1 \
            --http-port="$ODOO_HTTP_PORT" \
            --log-level=info
        ;;
    test)
        test_db_name="project_program_test_local"
        database_exists="$(psql -h "$ODOO_DB_HOST" -U "$ODOO_DB_USER" -d postgres -Atqc \
            "SELECT 1 FROM pg_database WHERE datname = '$test_db_name'")"
        module_state=""
        if [[ "$database_exists" == "1" ]]; then
            module_state="$(psql -h "$ODOO_DB_HOST" -U "$ODOO_DB_USER" -d "$test_db_name" -Atqc \
                "SELECT state FROM ir_module_module WHERE name = 'project_program'")"
        fi
        if [[ "$module_state" == "installed" ]]; then
            module_action=(-u project_program)
        else
            module_action=(-i project_program)
        fi
        odoo -d "$test_db_name" "${module_action[@]}" \
            --test-enable \
            --test-tags '/project_program' \
            --http-port="$ODOO_TEST_HTTP_PORT" \
            --stop-after-init \
            --log-level=warn
        ;;
    *)
        printf 'Usage: %s {setup|run|test}\n' "$0" >&2
        exit 2
        ;;
esac
