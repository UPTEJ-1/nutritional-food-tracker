import sqlite3
from datetime import date, timedelta

# Connect to database
conn = sqlite3.connect('nutrition_tracker.db')
cursor = conn.cursor()

# First, check if user_id 1 exists and what foods are available
cursor.execute('SELECT id, name FROM foods LIMIT 5')
foods = cursor.fetchall()
print('Available foods:')
for food in foods:
    print(f'  food_id {food[0]}: {food[1]}')

# Check if user exists
cursor.execute('SELECT id, username FROM users WHERE id = 1')
user = cursor.fetchone()
if user:
    print(f'\nUser found: id={user[0]}, username={user[1]}')
else:
    print('\nNo user with id=1. Cannot insert test data.')
    conn.close()
    exit(1)

# Check user goals
cursor.execute('SELECT daily_calories, daily_protein, daily_carbs, daily_fats FROM goals WHERE user_id = 1')
goal = cursor.fetchone()
if goal:
    print(f'User goals: {goal[0]} kcal, {goal[1]}g protein, {goal[2]}g carbs, {goal[3]}g fat')
else:
    print('No goals set for user. Using defaults.')

# Insert varied data for 7 past days
print('\nInserting test data for 7 days...')
for i in range(1, 8):
    day = date.today() - timedelta(days=i)
    try:
        # Breakfast: 100g (food_id 1)
        cursor.execute('INSERT INTO food_log (user_id, food_id, quantity_grams, meal_type, logged_date) VALUES (?, ?, ?, ?, ?)',
                       (1, 1, 100, 'Breakfast', day.isoformat()))
        # Lunch: 150g (food_id 2)
        cursor.execute('INSERT INTO food_log (user_id, food_id, quantity_grams, meal_type, logged_date) VALUES (?, ?, ?, ?, ?)',
                       (1, 2, 150, 'Lunch', day.isoformat()))
        # Dinner: 200g (food_id 3)
        cursor.execute('INSERT INTO food_log (user_id, food_id, quantity_grams, meal_type, logged_date) VALUES (?, ?, ?, ?, ?)',
                       (1, 3, 200, 'Dinner', day.isoformat()))
        day_str = day.strftime("%a, %b %d")
        print(f'  [OK] Inserted entries for {day_str}')
    except Exception as e:
        print(f'  [ERROR] Error on {day}: {e}')

conn.commit()
conn.close()
print('\nTest data insertion complete!')
