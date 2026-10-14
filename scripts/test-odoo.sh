#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts
network="program-test-${GITHUB_RUN_ID:-local}"
db="${network}-db"
trap 'docker rm -f "$db" >/dev/null 2>&1 || true; docker network rm "$network" >/dev/null 2>&1 || true' EXIT
docker network create "$network" >/dev/null
docker run -d --name "$db" --network "$network" -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_DB=postgres postgres:16 >/dev/null
for i in $(seq 1 40); do
  if docker exec "$db" pg_isready -U odoo >/dev/null 2>&1; then break; fi
  sleep 1
done
run_odoo() {
 docker run --rm --entrypoint odoo --network "$network" -v "$PWD:/mnt/extra-addons:ro" odoo:19.0 \
  --db_host="$db" --db_user=odoo --db_password=odoo -d program_test \
  --http-interface=0.0.0.0 --stop-after-init --test-enable --test-tags=/project_program \
  --without-demo=all --log-level=test "$@"
}
run_odoo -i project_program 2>&1 | tee artifacts/install.log
run_odoo -u project_program 2>&1 | tee artifacts/upgrade.log
python3 scripts/check-test-logs.py artifacts/install.log artifacts/upgrade.log
