#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts
network="odoo-v6-${GITHUB_RUN_ID:-local}"
db="odoo-v6-db-${GITHUB_RUN_ID:-local}"
trap 'docker rm -f "$db" >/dev/null 2>&1 || true; docker network rm "$network" >/dev/null 2>&1 || true' EXIT
docker network create "$network" >/dev/null
docker run -d --name "$db" --network "$network" -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_DB=postgres postgres:16 >/dev/null
ready=0
for i in $(seq 1 60); do
  if docker exec "$db" pg_isready -U odoo >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
test "$ready" -eq 1 || { echo 'Postgres did not start'; exit 1; }
run_odoo() {
  docker run --rm --entrypoint odoo --network "$network" -v "$PWD:/mnt/extra-addons:ro" odoo:19.0 \
    --db_host="$db" --db_user=odoo --db_password=odoo -d program_test \
    --stop-after-init --test-enable --test-tags=/project_program \
    --without-demo=all --log-level=test "$@"
}
run_odoo -i project_program 2>&1 | tee artifacts/install.log
run_odoo -u project_program 2>&1 | tee artifacts/upgrade.log
python3 scripts/check-test-logs.py artifacts/install.log artifacts/upgrade.log
