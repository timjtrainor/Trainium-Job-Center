#!/bin/bash

# Define the path to the .env file (one level up from scripts/)
ENV_FILE="$(dirname "$0")/../.env"

# Load env vars from .env if it exists
if [ -f "$ENV_FILE" ]; then
  echo "Loading configuration from .env..."
  export $(grep -v '^#' "$ENV_FILE" | xargs)
else
  echo "Warning: .env file not found at $ENV_FILE. Using defaults."
fi

# Set variables with defaults matching .env.example
DB_USER=${LANGFUSE_DB_USER:-langfuse}
DB_PASS=${LANGFUSE_DB_PASSWORD:-changeme}
DB_NAME=${LANGFUSE_DB_NAME:-langfuse}

echo "--------------------------------"
echo "Setting up LangFuse Database"
echo "--------------------------------"
echo "Target Container: trainium_db"
echo "User:             $DB_USER"
echo "Database:         $DB_NAME"
echo "--------------------------------"

# SQL Command Construction
# Note: usage of $do$ block prevents need for escaping quotes excessively
SQL_COMMAND="
DO
\$do\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = '$DB_USER') THEN

      CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASS';
      RAISE NOTICE 'Role $DB_USER created';
   ELSE
      RAISE NOTICE 'Role $DB_USER already exists';
   END IF;
END
\$do\$;

SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

ALTER DATABASE $DB_NAME OWNER TO $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
"

# Execute inside the docker container
# We pipe the constructed SQL into the psql command running inside the container
echo "$SQL_COMMAND" | docker exec -i trainium_db psql -U trainium_user -d postgres

echo "--------------------------------"
echo "Setup complete."
