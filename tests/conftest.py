import os

# Ensure required environment variables are present for tests
os.environ.setdefault("DATABASE_URL", "postgresql://fake:fake@localhost:5432/fake")
