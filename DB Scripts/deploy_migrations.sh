#!/bin/bash

# Deploy database migrations via Docker
# Usage: ./deploy_migrations.sh [migration_file.sql]

set -e  # Exit on error

CONTAINER_NAME="trainium_db"
DB_USER="trainium_user"
DB_NAME="trainium"

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Database Migration Deployment ===${NC}"

# Check if Docker container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}Error: PostgreSQL container '$CONTAINER_NAME' is not running${NC}"
    echo "Start it with: docker-compose up -d"
    exit 1
fi

if [ -z "$1" ]; then
    # No argument - deploy all pending migrations
    echo -e "${YELLOW}Deploying all pending migrations...${NC}"

    SQITCH_DIR="$(dirname "$0")/sqitch"

    # Deploy deduplication indexes
    echo -e "${GREEN}► Deploying deduplication indexes...${NC}"
    cat "$SQITCH_DIR/deploy/jobs_deduplication_indexes.sql" | \
        docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"

    # Deploy deduplicated view
    echo -e "${GREEN}► Deploying deduplicated view...${NC}"
    cat "$SQITCH_DIR/deploy/jobs_deduplicated_view.sql" | \
        docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"

    echo -e "${GREEN}✓ All migrations deployed successfully!${NC}"
else
    # Deploy specific migration
    MIGRATION_FILE="$1"

    if [ ! -f "$MIGRATION_FILE" ]; then
        echo -e "${RED}Error: Migration file '$MIGRATION_FILE' not found${NC}"
        exit 1
    fi

    echo -e "${GREEN}► Deploying $MIGRATION_FILE...${NC}"
    cat "$MIGRATION_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"
    echo -e "${GREEN}✓ Migration deployed successfully!${NC}"
fi

# Show deduplication status
echo -e "\n${YELLOW}=== Deduplication Status ===${NC}"
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT
    COUNT(*) as total_jobs,
    COUNT(DISTINCT canonical_key) as unique_jobs_by_key,
    COUNT(*) FILTER (WHERE canonical_key IS NOT NULL) as jobs_with_canonical_key,
    COUNT(*) FILTER (WHERE fingerprint IS NOT NULL) as jobs_with_fingerprint
FROM jobs;
EOF

echo -e "\n${GREEN}Done!${NC}"
