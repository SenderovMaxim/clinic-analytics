#!/bin/bash
set -e
DUMP_FILE="/docker-entrypoint-initdb.d/demo_server_20260507.dump"

# Создаем read-only пользователя для безопасности
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE USER cliniciq_readonly WITH PASSWORD 'cliniciq_readonly_pass';
  GRANT CONNECT ON DATABASE cliniciq2_db TO cliniciq_readonly;
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO cliniciq_readonly;
  GRANT USAGE ON SCHEMA public TO cliniciq_readonly;
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO cliniciq_readonly;
EOSQL

if [ -f "$DUMP_FILE" ]; then
  echo "🔄 Restoring dump..."
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$DUMP_FILE"
  echo "✅ Dump restored successfully."
else
  echo "⚠️  No dump file found at $DUMP_FILE"
fi