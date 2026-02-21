#!/usr/bin/env bash
set -euo pipefail

if ! [[ "$DB_APP_USER" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
  echo "Invalid DB_APP_USER: $DB_APP_USER"
  exit 1
fi

echo "Waiting for db to be ready..."

until pg_isready -h db -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  sleep 1
done

echo "Bootstrapping database..."

psql -h db -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_APP_USER}') THEN
    EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', '${DB_APP_USER}', '${DB_APP_PASSWORD}');
  END IF;
END
\$\$;

GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${DB_APP_USER};

\connect ${POSTGRES_DB}

GRANT USAGE, CREATE ON SCHEMA public TO ${DB_APP_USER};
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ${DB_APP_USER};
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO ${DB_APP_USER};

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${DB_APP_USER};

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO ${DB_APP_USER};
SQL

echo "Bootstrap complete."