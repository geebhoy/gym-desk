
import os
import sqlite3
from pathlib import Path


DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    str(Path(__file__).resolve().parent / "gym_desk.db")
)


def initialize_database():
    # Create the database folder if it does not exist.
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

    # Connect to the configured database.
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        # Create the members table if it does not exist.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                code TEXT UNIQUE,
                expires TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create the payments table if it does not exist.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                mid TEXT,
                amount REAL NOT NULL,
                method TEXT,
                months INTEGER,
                date TEXT,
                start_date TEXT,
                plan TEXT,
                name TEXT
            )
        """)

        # Create the visits table if it does not exist.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id TEXT PRIMARY KEY,
                mid TEXT,
                check_in INTEGER,
                check_out INTEGER
            )
        """)

        # Create the membership plans table if it does not exist.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                months INTEGER NOT NULL,
                price REAL NOT NULL
            )
        """)

        connection.commit()

    finally:
        connection.close()