
import sqlite3

# Connect to the Gym Desk database
connection = sqlite3.connect("database/gym_desk.db")

# Create the members table
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

# Create the payments table
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

# Create the visits table
connection.execute("""
    CREATE TABLE IF NOT EXISTS visits (
        id TEXT PRIMARY KEY,
        mid TEXT,
        check_in INTEGER,
        check_out INTEGER
    )
""")

# Create the membership plans table
connection.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        months INTEGER NOT NULL,
        price REAL NOT NULL
    )
""")

# Save the changes
connection.commit()

# Close the database connection
connection.close()

print("Gym Desk database tables created successfully!")