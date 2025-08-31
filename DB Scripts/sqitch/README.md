# Sqitch Database Change Management

This directory contains the Sqitch configuration and migration scripts for managing your PostgreSQL database schema.

## What is Sqitch?
[Sqitch](https://sqitch.org/) is a database change management system that uses a VCS-like approach to track, deploy, revert, and verify schema changes. It is designed to work with various databases, including PostgreSQL.

## Prerequisites
- PostgreSQL installed and running
- Sqitch installed ([installation guide](https://sqitch.org/download/))
- Node.js (optional, for dotenv or scripting)

## Environment Variables
All database credentials and connection info are stored in your project's root `.env` file. **Do not hardcode credentials in config files.**

Example `.env`:
```
POSTGRES_USER=trainium_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=trainium
POSTGRES_PORT=5434
```

## Constructing the Database URI
Sqitch expects a single environment variable `PG_LOCAL_URI` for the database connection. Construct it from your `.env` variables before running Sqitch:

```
export $(cat .env | xargs) # Loads all .env variables into your shell
export PG_LOCAL_URI="db:pg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
```

## Running Sqitch Commands
All Sqitch commands should be run from the `DB Scripts/sqitch/` directory. Example commands:

- **Deploy changes:**
  ```
  sqitch deploy
  ```
- **Revert last change:**
  ```
  sqitch revert
  ```
- **Verify deployment:**
  ```
  sqitch verify
  ```

## Security Best Practices
- Never commit `.env` or files containing secrets to version control.
- `.gitignore` should include `.env` and `sqitch.conf`.
- Use environment variables for all credentials.

## Troubleshooting
- If Sqitch cannot connect, ensure `PG_LOCAL_URI` is set and exported in your shell.
- Check that PostgreSQL is running and accessible on the specified port.
- For more help, see the [Sqitch documentation](https://sqitch.org/docs/).

## References
- [Sqitch Documentation](https://sqitch.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Contact your project maintainer for further assistance.**

