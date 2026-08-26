"""
Initializes a small SQLite database with demo data so the Agent's SQL tool
has something realistic to query.

Run with: python -m app.db.init_db
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "sample.db")


def init_db(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    cur.execute("DROP TABLE IF EXISTS employees")
    cur.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            hire_date TEXT NOT NULL,
            salary REAL NOT NULL
        )
    """)

    products = [
        (1, "Acme Pro Subscription", "Software", 49.99, 999),
        (2, "Acme Team Subscription", "Software", 199.99, 999),
        (3, "Wireless Mouse", "Hardware", 29.99, 150),
        (4, "Mechanical Keyboard", "Hardware", 89.99, 75),
        (5, "USB-C Hub", "Hardware", 39.99, 200),
        (6, "Noise-Cancelling Headphones", "Hardware", 149.99, 60),
        (7, "Acme Enterprise Subscription", "Software", 999.99, 999),
    ]
    cur.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)

    employees = [
        (1, "Priya Sharma", "Engineering", "2022-03-14", 95000),
        (2, "Daniel Kim", "Sales", "2021-07-01", 72000),
        (3, "Maria Garcia", "Engineering", "2023-01-09", 88000),
        (4, "James Wilson", "Support", "2020-11-23", 61000),
        (5, "Aisha Khan", "Engineering", "2024-02-19", 91000),
    ]
    cur.executemany("INSERT INTO employees VALUES (?,?,?,?,?)", employees)

    conn.commit()
    conn.close()
    print(f"Initialized demo database at {db_path}")
    print(f"  - {len(products)} products")
    print(f"  - {len(employees)} employees")


if __name__ == "__main__":
    init_db()
