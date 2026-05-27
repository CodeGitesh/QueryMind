#!/bin/bash
# ============================================================
# Database initialization script
# Runs AFTER Postgres initializes the querymind database.
# Seeds all three schemas: ecommerce, hr, finance.
# ============================================================
set -e

echo "🌱 Seeding QueryMind schemas..."

# E-Commerce schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -f /docker-entrypoint-initdb.d/seeds/ecommerce.sql
echo "✅ E-Commerce schema seeded"

# HR schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -f /docker-entrypoint-initdb.d/seeds/hr.sql
echo "✅ HR schema seeded"

# Finance schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -f /docker-entrypoint-initdb.d/seeds/finance.sql
echo "✅ Finance schema seeded"

# Create read-only role for query execution
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'querymind_reader') THEN
            CREATE ROLE querymind_reader;
        END IF;
    END
    \$\$;

    GRANT USAGE ON SCHEMA ecommerce TO querymind_reader;
    GRANT USAGE ON SCHEMA hr TO querymind_reader;
    GRANT USAGE ON SCHEMA finance TO querymind_reader;
    GRANT SELECT ON ALL TABLES IN SCHEMA ecommerce TO querymind_reader;
    GRANT SELECT ON ALL TABLES IN SCHEMA hr TO querymind_reader;
    GRANT SELECT ON ALL TABLES IN SCHEMA finance TO querymind_reader;
    ALTER DEFAULT PRIVILEGES IN SCHEMA ecommerce GRANT SELECT ON TABLES TO querymind_reader;
    ALTER DEFAULT PRIVILEGES IN SCHEMA hr GRANT SELECT ON TABLES TO querymind_reader;
    ALTER DEFAULT PRIVILEGES IN SCHEMA finance GRANT SELECT ON TABLES TO querymind_reader;
EOSQL

echo "✅ Read-only role 'querymind_reader' configured"
echo "🚀 Database initialization complete!"
