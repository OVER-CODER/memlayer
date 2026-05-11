#!/usr/bin/env python
"""
Database initialization script.
Creates PostgreSQL database and pgvector extension.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"→ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description}")
            return True
        else:
            print(f"✗ {description}")
            print(f"  Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ {description}")
        print(f"  Exception: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("MemLayer Database Initialization")
    print("=" * 60)

    # Check if PostgreSQL is running
    if not run_command("pg_isready", "Checking PostgreSQL connection"):
        print("\nPostgreSQL is not running. Please start it first.")
        return 1

    # Create database
    db_name = "memlayer_dev"
    run_command(
        f"createdb {db_name} 2>/dev/null || echo 'Database may already exist'",
        "Creating database",
    )

    # Create pgvector extension
    run_command(
        f"psql {db_name} -c 'CREATE EXTENSION IF NOT EXISTS vector;'",
        "Installing pgvector extension",
    )

    # Create vector index for faster similarity search
    run_command(
        f"""psql {db_name} -c \"CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);\"  """,
        "Creating vector index",
    )

    print("\n" + "=" * 60)
    print("✓ Database initialization complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Copy .env.example to .env and update GEMINI_API_KEY")
    print("2. Run: poetry install")
    print("3. Run: python -m app.main")

    return 0


if __name__ == "__main__":
    sys.exit(main())
