"""
Disclosed test-data helper: inserts food_log rows for ncea_tester
(user_id 4, goal 2500 kcal) on three recent dates so the history page
genuinely renders one green (on-track), one amber (under) and one red
(over) row. Uses Oats (food_id 4, 389 kcal/100g). Not fabricated app
output -- real rows the app then reads and computes normally.
"""
import sqlite3

conn = sqlite3.connect('nutrition_tracker.db')
cursor = conn.cursor()

# (logged_date, quantity_grams) -> expected kcal vs 2500 goal
rows = [
    ('2026-07-01', 643, 'Breakfast'),  # ~2501 kcal -> on-track (green)
    ('2026-06-30', 300, 'Breakfast'),  # ~1167 kcal -> under (amber)
    ('2026-06-29', 900, 'Dinner'),     # ~3501 kcal -> over (red)
]

for logged_date, qty, meal in rows:
    cursor.execute(
        'INSERT INTO food_log (user_id, food_id, quantity_grams, '
        'meal_type, logged_date) VALUES (?, ?, ?, ?, ?)',
        (4, 4, qty, meal, logged_date)
    )
    print(f'  Inserted {qty}g Oats on {logged_date} '
          f'(~{qty * 389 / 100:.0f} kcal)')

conn.commit()
conn.close()
print('History test data inserted for user 4.')
