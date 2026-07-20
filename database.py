import os
import shutil
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'nutrition_tracker.db')
LEGACY_DB_PATH = os.path.join(BASE_DIR, 'nutrition_tracker.db')


def ensure_database_location():
    """Create database/ folder and migrate legacy root DB file if needed."""
    os.makedirs(DATABASE_DIR, exist_ok=True)
    if os.path.isfile(LEGACY_DB_PATH) and not os.path.isfile(DATABASE_PATH):
        shutil.move(LEGACY_DB_PATH, DATABASE_PATH)


def get_db_connection():
    """
    Establishes and returns a SQLite3 database connection.
    Configures row factory to return rows as sqlite3.Row objects for dict-like access.
    """
    ensure_database_location()
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys = ON')
    return connection


def migrate_schema(cursor):
    """Apply incremental schema updates for existing databases."""
    cursor.execute('PRAGMA table_info(food_log)')
    columns = {row[1] for row in cursor.fetchall()}
    if 'is_favourite' not in columns:
        cursor.execute(
            'ALTER TABLE food_log ADD COLUMN is_favourite INTEGER NOT NULL DEFAULT 0'
        )


def create_tables():
    """
    Creates all necessary database tables if they do not already exist.
    Tables: users, foods, food_log, goals
    """
    ensure_database_location()
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            calories_per_100g REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fats REAL NOT NULL,
            fibre REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_id INTEGER NOT NULL,
            quantity_grams REAL NOT NULL,
            meal_type TEXT NOT NULL,
            logged_date DATE NOT NULL DEFAULT CURRENT_DATE,
            is_favourite INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (food_id) REFERENCES foods(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            daily_calories REAL NOT NULL DEFAULT 2000,
            daily_protein REAL NOT NULL DEFAULT 150,
            daily_carbs REAL NOT NULL DEFAULT 250,
            daily_fats REAL NOT NULL DEFAULT 65,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    migrate_schema(cursor)
    connection.commit()
    connection.close()


def seed_foods():
    """
    Populates the foods table with 20 foods per 100g (USDA FoodData Central values).
    Only seeds if foods table is empty to avoid duplicate entries.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('SELECT COUNT(*) FROM foods')
    if cursor.fetchone()[0] > 0:
        connection.close()
        return

    foods_data = [
        ('Chicken Breast', 165, 31, 0, 3.6, 0),
        ('Brown Rice (cooked)', 111, 2.6, 23, 0.9, 1.8),
        ('White Rice (cooked)', 130, 2.7, 28, 0.3, 0.4),
        ('Oats', 389, 17, 66, 6.9, 10),
        ('Eggs (whole)', 155, 13, 1.1, 11, 0),
        ('Salmon', 208, 20, 0, 13, 0),
        ('Tuna (canned in water)', 96, 21, 0, 0.8, 0),
        ('Greek Yogurt (plain)', 59, 10, 3.3, 0.4, 0),
        ('Banana', 89, 1.1, 23, 0.3, 2.6),
        ('Apple', 52, 0.3, 14, 0.2, 2.4),
        ('Broccoli', 34, 2.8, 7, 0.4, 2.4),
        ('Sweet Potato', 86, 1.6, 20, 0.1, 3),
        ('Whole Milk', 61, 3.2, 4.8, 3.3, 0),
        ('Cheddar Cheese', 403, 23, 3.3, 33, 0),
        ('Bread (wholegrain)', 227, 9, 43, 3.3, 6.3),
        ('Pasta (cooked)', 131, 5, 25, 1.1, 1.8),
        ('Beef Mince (lean)', 182, 26, 0, 8, 0),
        ('Peanut Butter', 588, 25, 20, 50, 6),
        ('Almonds', 579, 21, 22, 50, 12),
        ('Protein Powder (whey)', 417, 80, 7, 8, 0),
    ]

    cursor.executemany('''
        INSERT INTO foods (name, calories_per_100g, protein, carbs, fats, fibre)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', foods_data)

    connection.commit()
    connection.close()


if __name__ == '__main__':
    create_tables()
    seed_foods()
    print(f'Database ready at {DATABASE_PATH}')
