import sqlite3
import os

# Database connection configuration
DATABASE_PATH = 'nutrition_tracker.db'


def get_db_connection():
    """
    Establishes and returns a SQLite3 database connection.
    Configures row factory to return rows as sqlite3.Row objects for dict-like access.
    """
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    """
    Creates all necessary database tables if they do not already exist.
    Tables: users, foods, food_log, goals
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    # Users table: stores user account information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Foods table: stores nutritional information for foods
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            calories_per_100g REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fats REAL NOT NULL,
            fibre REAL NOT NULL,
            is_favourite INTEGER NOT NULL DEFAULT 0
        )
    ''')

    # If this db was created earlier without is_favourite, try to add it.
    cursor.execute("PRAGMA table_info(foods)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    if 'is_favourite' not in existing_cols:
        try:
            cursor.execute('ALTER TABLE foods ADD COLUMN is_favourite INTEGER NOT NULL DEFAULT 0')
            print('Added is_favourite column to foods')
        except Exception:
            pass

    # Food log table: tracks what food each user consumed and when
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_id INTEGER NOT NULL,
            quantity_grams REAL NOT NULL,
            meal_type TEXT NOT NULL,
            logged_date DATE NOT NULL DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (food_id) REFERENCES foods(id)
        )
    ''')

    # Ensure is_favourite column exists on food_log (added later in project history)
    cursor.execute("PRAGMA table_info(food_log)")
    cols = [r[1] for r in cursor.fetchall()]
    if 'is_favourite' not in cols:
        try:
            cursor.execute('ALTER TABLE food_log ADD COLUMN is_favourite INTEGER NOT NULL DEFAULT 0')
            print('Added is_favourite column to food_log')
        except Exception:
            # Older SQLite versions may not support ALTER table in complex ways,
            # but a simple ADD COLUMN should work. If it fails, skip silently.
            pass

    # Goals table: stores daily nutritional goals for each user
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

    connection.commit()
    connection.close()
    print("Tables created successfully!")


def seed_foods():
    """
    Populates the foods table with 20 real foods and their accurate nutritional data per 100g.
    Only seeds if foods table is empty to avoid duplicate entries.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    # Check if foods already exist
    cursor.execute('SELECT COUNT(*) FROM foods')
    if cursor.fetchone()[0] > 0:
        print("Foods already seeded, skipping...")
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
    print(f"Seeded {len(foods_data)} foods successfully!")


if __name__ == '__main__':
    create_tables()
    seed_foods()
