from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, create_tables, seed_foods
from models import FoodEntry, NutritionCalculator
from datetime import date, timedelta
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

DEFAULT_GOALS = {
    'daily_calories': 2000,
    'daily_protein': 150,
    'daily_carbs': 250,
    'daily_fats': 65,
}

MEAL_ORDER = ['Breakfast', 'Lunch', 'Dinner', 'Snack']


def validate_registration(username, password):
    username = (username or '').strip()
    if len(username) < 3 or len(username) > 30:
        return 'Username must be between 3 and 30 characters.'
    if not password:
        return 'Please fill in all fields.'
    if len(password) < 8:
        return 'Password must be at least 8 characters.'
    return None


def favourite_food_ids(cursor, user_id):
    cursor.execute('''
        SELECT DISTINCT food_id FROM food_log
        WHERE user_id = ? AND is_favourite = 1
    ''', (user_id,))
    return {row['food_id'] for row in cursor.fetchall()}


def search_foods(cursor, user_id, query):
    """Search foods with SQL LIKE; favourites appear first in results."""
    favourites = favourite_food_ids(cursor, user_id)
    like_term = f'%{query.strip()}%'
    cursor.execute('''
        SELECT id, name, calories_per_100g, protein, carbs, fats
        FROM foods
        WHERE name LIKE ? COLLATE NOCASE
        ORDER BY name ASC
        LIMIT 50
    ''', (like_term,))
    rows = cursor.fetchall()
    results = []
    for row in rows:
        results.append({
            'id': row['id'],
            'name': row['name'],
            'calories_per_100g': row['calories_per_100g'],
            'protein': row['protein'],
            'carbs': row['carbs'],
            'fats': row['fats'],
            'is_favourite': row['id'] in favourites,
        })
    results.sort(key=lambda item: (not item['is_favourite'], item['name'].lower()))
    return results


def init_database():
    """Ensure schema and starter food catalog exist before handling requests."""
    create_tables()
    seed_foods()


def goals_from_row(goals_row):
    if goals_row:
        return {
            'daily_calories': goals_row['daily_calories'],
            'daily_protein': goals_row['daily_protein'],
            'daily_carbs': goals_row['daily_carbs'],
            'daily_fats': goals_row['daily_fats'],
        }
    return dict(DEFAULT_GOALS)


def fetch_user_goals(cursor, user_id):
    cursor.execute(
        'SELECT daily_calories, daily_protein, daily_carbs, daily_fats '
        'FROM goals WHERE user_id = ?',
        (user_id,),
    )
    return goals_from_row(cursor.fetchone())

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'


# User class for Flask-Login
class User(UserMixin):
    """
    User class that integrates with Flask-Login.
    Implements required UserMixin properties and methods for session management.
    """
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    @property
    def is_authenticated(self):
        """Returns True as all User instances are authenticated."""
        return True

    @property
    def is_active(self):
        """Returns True as all User instances are active."""
        return True

    @property
    def is_anonymous(self):
        """Returns False as User instances are not anonymous."""
        return False

    def get_id(self):
        """Returns the user id as a string for Flask-Login."""
        return str(self.id)


# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """
    Loads a user from the database by their ID.
    Called by Flask-Login to restore user sessions.
    Returns: User object if found, None otherwise
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    connection.close()

    if user_data:
        return User(user_data['id'], user_data['username'], user_data['email'])
    return None


# Calculate nutrition function: multiplies nutritional values by quantity
def calculate_nutrition(food_id, quantity_grams):
    """
    Calculates the nutritional values for a given food based on quantity in grams.

    Parameters:
        food_id (int): The ID of the food from the foods table
        quantity_grams (float): The quantity of food in grams to log

    Returns:
        dict: A dictionary containing nutritional values with keys:
              calories, protein, carbs, fats, fibre
              All values are multiplied by (quantity_grams / 100) from the per-100g values

    Raises:
        ValueError: If quantity_grams is not between 0 and 2000
    """
    # Validate quantity
    if quantity_grams <= 0 or quantity_grams > 2000:
        raise ValueError('Quantity must be between 1 and 2000 grams.')

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT calories_per_100g, protein, carbs, fats, fibre FROM foods WHERE id = ?', (food_id,))
    food_data = cursor.fetchone()
    connection.close()

    if not food_data:
        raise ValueError('Food not found in database.')

    # Calculate nutrition by multiplying per-100g values by quantity factor
    multiplier = quantity_grams / 100
    return {
        'calories': food_data['calories_per_100g'] * multiplier,
        'protein': food_data['protein'] * multiplier,
        'carbs': food_data['carbs'] * multiplier,
        'fats': food_data['fats'] * multiplier,
        'fibre': food_data['fibre'] * multiplier,
    }


# Root route: redirects to dashboard if authenticated, otherwise to login
@app.route('/')
def index():
    """
    Root route that handles unauthenticated and authenticated users.
    Redirects authenticated users to dashboard, others to login.
    Returns: redirect to dashboard or login
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# Register route: GET renders form, POST creates new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles user registration.
    GET: Renders the registration form template.
    POST: Validates input, hashes password, creates new user in database.
    Returns: render_template on GET, redirect to login on successful POST, render_template with error on failed POST
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('register'))

        username = username.strip()
        validation_error = validate_registration(username, password)
        if validation_error:
            flash(validation_error, 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if username already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('Username already taken.', 'danger')
            connection.close()
            return redirect(url_for('register'))

        # Check if email already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            flash('Email already registered.', 'danger')
            connection.close()
            return redirect(url_for('register'))

        # Hash password and insert new user
        password_hash = generate_password_hash(password)
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            connection.commit()
            # Log the new user in immediately using the same pattern as
            # the login() route, so they skip a manual login step.
            new_user = User(cursor.lastrowid, username, email)
            login_user(new_user)
            flash(f'Welcome, {username}! Your account has been created.',
                  'success')
            connection.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
            connection.close()
            return redirect(url_for('register'))

    return render_template('register.html')


# Login route: GET renders form, POST authenticates user
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    GET: Renders the login form template.
    POST: Authenticates user credentials and creates session.
    Returns: render_template on GET, redirect to dashboard on successful POST, render_template with error on failed POST
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('login'))

        connection = get_db_connection()
        cursor = connection.cursor()

        # Look up user by username
        cursor.execute('SELECT id, username, email, password_hash FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        connection.close()

        # Verify user exists and password is correct
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['id'], user_data['username'], user_data['email'])
            login_user(user)
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


# Logout route: clears session and redirects to login
@app.route('/logout')
@login_required
def logout():
    """
    Handles user logout.
    Clears the user session and redirects to login page.
    Returns: redirect to login
    """
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# Dashboard route: protected route for logged-in users
@app.route('/dashboard')
@login_required
def dashboard():
    """
    Displays the user dashboard with today's food log and nutritional goals.
    Queries food_log entries for today, calculates totals, and retrieves user goals.
    Calculates percentage of each macro reached (capped at 100%).
    Returns: render_template of dashboard.html with nutrition data and goals
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    today = date.today()

    # Query today's food log entries with food names
    cursor.execute('''
        SELECT fl.id, fl.food_id, fl.is_favourite, f.name, fl.quantity_grams,
               fl.meal_type, f.calories_per_100g, f.protein, f.carbs, f.fats
        FROM food_log fl
        JOIN foods f ON fl.food_id = f.id
        WHERE fl.user_id = ? AND fl.logged_date = ?
        ORDER BY fl.id DESC
    ''', (current_user.id, today.isoformat()))
    today_foods = cursor.fetchall()

    goals = fetch_user_goals(cursor, current_user.id)
    connection.close()

    food_entries = []
    meals_grouped = {meal: [] for meal in MEAL_ORDER}
    meal_subtotals = {
        meal: {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0}
        for meal in MEAL_ORDER
    }

    for food in today_foods:
        multiplier = food['quantity_grams'] / 100
        calories = food['calories_per_100g'] * multiplier
        protein = food['protein'] * multiplier
        carbs = food['carbs'] * multiplier
        fats = food['fats'] * multiplier

        food_entries.append(FoodEntry(
            food['food_id'],
            food['name'],
            food['quantity_grams'],
            food['meal_type'],
            calories,
            protein,
            carbs,
            fats,
        ))

        entry = {
            'id': food['id'],
            'food_id': food['food_id'],
            'name': food['name'],
            'quantity_grams': food['quantity_grams'],
            'meal_type': food['meal_type'],
            'calories': round(calories, 1),
            'protein': round(protein, 1),
            'carbs': round(carbs, 1),
            'fats': round(fats, 1),
            'is_favourite': bool(food['is_favourite']),
        }
        meal_key = food['meal_type'] if food['meal_type'] in meals_grouped else 'Snack'
        meals_grouped[meal_key].append(entry)
        meal_subtotals[meal_key]['calories'] += calories
        meal_subtotals[meal_key]['protein'] += protein
        meal_subtotals[meal_key]['carbs'] += carbs
        meal_subtotals[meal_key]['fats'] += fats

    calculator = NutritionCalculator(food_entries)
    totals = calculator.get_daily_totals()
    goal_pct = calculator.get_goal_percentages(goals)
    progress = {
        'calories': int(goal_pct['calories_percent']),
        'protein': int(goal_pct['protein_percent']),
        'carbs': int(goal_pct['carbs_percent']),
        'fats': int(goal_pct['fats_percent']),
    }
    macro_balance = calculator.get_macro_balance()

    for meal in MEAL_ORDER:
        for key in meal_subtotals[meal]:
            meal_subtotals[meal][key] = round(meal_subtotals[meal][key], 1)

    return render_template(
        'dashboard.html',
        username=current_user.username,
        total_calories=totals['total_calories'],
        total_protein=totals['total_protein'],
        total_carbs=totals['total_carbs'],
        total_fats=totals['total_fats'],
        goals=goals,
        progress=progress,
        macro_balance=macro_balance,
        meals_grouped=meals_grouped,
        meal_subtotals=meal_subtotals,
        meal_order=MEAL_ORDER,
    )


# Log food route: GET shows form, POST logs food to database
@app.route('/log-food', methods=['GET', 'POST'])
@login_required
def log_food():
    """
    Handles food logging for users.
    GET: Queries all foods from database and renders log_food.html with food list.
    POST: Validates input, calculates nutrition, inserts food_log entry with user_id, food_id, quantity, meal_type, and today's date.
    Returns: render_template on GET, redirect to dashboard on successful POST, render_template with error on failed POST
    """
    if request.method == 'POST':
        food_id = request.form.get('food_id')
        quantity_grams = request.form.get('quantity_grams')
        meal_type = request.form.get('meal_type')

        # Validate input
        if not food_id or not quantity_grams or not meal_type:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('log_food'))

        try:
            food_id = int(food_id)
            quantity_grams = float(quantity_grams)
        except ValueError:
            flash('Invalid food ID or quantity.', 'danger')
            return redirect(url_for('log_food'))

        # Calculate nutrition values
        try:
            nutrition = calculate_nutrition(food_id, quantity_grams)
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('log_food'))

        # Insert food log entry
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute('''
                INSERT INTO food_log (user_id, food_id, quantity_grams, meal_type, logged_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (current_user.id, food_id, quantity_grams, meal_type, date.today().isoformat()))
            connection.commit()
            flash(f'Food logged successfully! ({nutrition["calories"]:.1f} kcal)', 'success')
            connection.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Failed to log food: {str(e)}', 'danger')
            connection.close()
            return redirect(url_for('log_food'))

    return render_template('log_food.html')


@app.route('/api/foods/search')
@login_required
def api_food_search():
    """JSON food search using SQL LIKE; favourites listed first."""
    query = request.args.get('q', '').strip()
    connection = get_db_connection()
    cursor = connection.cursor()
    if not query:
        cursor.execute('''
            SELECT id, name, calories_per_100g, protein, carbs, fats
            FROM foods ORDER BY name ASC LIMIT 50
        ''')
        favourites = favourite_food_ids(cursor, current_user.id)
        foods = [{
            'id': row['id'],
            'name': row['name'],
            'calories_per_100g': row['calories_per_100g'],
            'protein': row['protein'],
            'carbs': row['carbs'],
            'fats': row['fats'],
            'is_favourite': row['id'] in favourites,
        } for row in cursor.fetchall()]
        foods.sort(key=lambda item: (not item['is_favourite'], item['name'].lower()))
    else:
        foods = search_foods(cursor, current_user.id, query)
    connection.close()
    return jsonify({'foods': foods})


@app.route('/toggle-favourite/<int:entry_id>', methods=['POST'])
@login_required
def toggle_favourite(entry_id):
    """Star or unstar a logged food entry (marks food as favourite for search)."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        'SELECT user_id, is_favourite FROM food_log WHERE id = ?',
        (entry_id,),
    )
    entry = cursor.fetchone()
    if not entry or entry['user_id'] != current_user.id:
        flash('Food entry not found or unauthorized.', 'danger')
        connection.close()
        return redirect(url_for('dashboard'))

    new_value = 0 if entry['is_favourite'] else 1
    cursor.execute(
        'UPDATE food_log SET is_favourite = ? WHERE id = ?',
        (new_value, entry_id),
    )
    connection.commit()
    connection.close()
    flash('Favourite updated.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/profile')
@login_required
def profile():
    """Simple profile page linked from the navbar."""
    return render_template(
        'profile.html',
        username=current_user.username,
        email=current_user.email,
    )


# Delete food log entry route: removes a logged food entry
@app.route('/delete-food-log/<int:entry_id>', methods=['POST'])
@login_required
def delete_food_log(entry_id):
    """
    Deletes a food log entry for the current user.
    Verifies that the entry belongs to the current user before deletion.
    Returns: redirect to dashboard with success or error message
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    # Verify the entry belongs to current user
    cursor.execute('SELECT user_id FROM food_log WHERE id = ?', (entry_id,))
    entry = cursor.fetchone()

    if not entry or entry['user_id'] != current_user.id:
        flash('Food entry not found or unauthorized.', 'danger')
        connection.close()
        return redirect(url_for('dashboard'))

    try:
        cursor.execute('DELETE FROM food_log WHERE id = ?', (entry_id,))
        connection.commit()
        flash('Food entry deleted successfully.', 'success')
    except Exception as e:
        flash(f'Failed to delete entry: {str(e)}', 'danger')
    finally:
        connection.close()

    return redirect(url_for('dashboard'))


# Goals route: GET shows form, POST updates user goals
@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    """
    Handles user nutritional goals management.
    GET: Queries user's current goals and renders goals.html form.
    POST: Validates input and updates or inserts user goals into the database.
    Returns: render_template on GET, redirect to dashboard on successful POST with success message
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == 'POST':
        daily_calories = request.form.get('daily_calories')
        daily_protein = request.form.get('daily_protein')
        daily_carbs = request.form.get('daily_carbs')
        daily_fats = request.form.get('daily_fats')

        # Validate input
        if not all([daily_calories, daily_protein, daily_carbs, daily_fats]):
            flash('Please fill in all fields.', 'danger')
            connection.close()
            return redirect(url_for('goals'))

        try:
            daily_calories = float(daily_calories)
            daily_protein = float(daily_protein)
            daily_carbs = float(daily_carbs)
            daily_fats = float(daily_fats)
        except ValueError:
            flash('Please enter valid numbers for all fields.', 'danger')
            connection.close()
            return redirect(url_for('goals'))

        # Server-side validation: the goals.html form has client-side
        # min attributes, but the client cannot be trusted, so re-check
        # here. Reject non-positive macros and calories below 500.
        if (daily_calories < 500 or daily_protein <= 0
                or daily_carbs <= 0 or daily_fats <= 0):
            flash('Daily calories must be at least 500, and all goals '
                  'must be greater than 0.', 'danger')
            connection.close()
            return redirect(url_for('goals'))

        # Check if goals exist for user
        cursor.execute('SELECT id FROM goals WHERE user_id = ?', (current_user.id,))
        existing_goal = cursor.fetchone()

        try:
            if existing_goal:
                # Update existing goals
                cursor.execute('''
                    UPDATE goals
                    SET daily_calories = ?, daily_protein = ?, daily_carbs = ?, daily_fats = ?
                    WHERE user_id = ?
                ''', (daily_calories, daily_protein, daily_carbs, daily_fats, current_user.id))
            else:
                # Insert new goals
                cursor.execute('''
                    INSERT INTO goals (user_id, daily_calories, daily_protein, daily_carbs, daily_fats)
                    VALUES (?, ?, ?, ?, ?)
                ''', (current_user.id, daily_calories, daily_protein, daily_carbs, daily_fats))
            connection.commit()
            flash('Goals updated successfully!', 'success')
            connection.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Failed to update goals: {str(e)}', 'danger')
            connection.close()
            return redirect(url_for('goals'))

    # GET request: fetch current goals
    current_goals = fetch_user_goals(cursor, current_user.id)
    connection.close()

    return render_template('goals.html', current_goals=current_goals)


# History route: displays nutrition data for the last 14 days
@app.route('/history')
@login_required
def history():
    """
    Displays user's nutrition history for the last 14 days.
    Queries food_log entries grouped by date, calculates daily totals,
    determines status (on-track/over/under), and displays in a table.
    Also provides charts for calorie trends and macro breakdown.
    Returns: render_template of history.html with daily summaries and goals
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    today = date.today()
    fourteen_days_ago = today - timedelta(days=13)

    # Query food_log entries for the last 14 days (inclusive)
    cursor.execute('''
        SELECT fl.logged_date, f.calories_per_100g, f.protein, f.carbs, f.fats,
               fl.quantity_grams
        FROM food_log fl
        JOIN foods f ON fl.food_id = f.id
        WHERE fl.user_id = ? AND fl.logged_date BETWEEN ? AND ?
        ORDER BY fl.logged_date DESC
    ''', (current_user.id, fourteen_days_ago.isoformat(), today.isoformat()))
    food_entries = cursor.fetchall()

    goals = fetch_user_goals(cursor, current_user.id)
    connection.close()

    # Group entries by date and calculate daily totals
    daily_data = {}
    for entry in food_entries:
        log_date = entry['logged_date']
        multiplier = entry['quantity_grams'] / 100

        if log_date not in daily_data:
            daily_data[log_date] = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fats': 0
            }

        daily_data[log_date]['calories'] += entry['calories_per_100g'] * multiplier
        daily_data[log_date]['protein'] += entry['protein'] * multiplier
        daily_data[log_date]['carbs'] += entry['carbs'] * multiplier
        daily_data[log_date]['fats'] += entry['fats'] * multiplier

    def status_for_calories(calories):
        if abs(calories - goals['daily_calories']) <= 100:
            return 'on-track'
        if calories > goals['daily_calories'] + 100:
            return 'over'
        return 'under'

    daily_summaries = []
    chart_data = []
    today_totals = {'protein': 0, 'carbs': 0, 'fats': 0, 'calories': 0}

    for n in range(14):
        single_date = today - timedelta(days=n)
        date_key = single_date.isoformat()
        day_totals = daily_data.get(date_key, {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fats': 0,
        })

        summary = {
            'date': single_date,
            'calories': round(day_totals['calories'], 1),
            'protein': round(day_totals['protein'], 1),
            'carbs': round(day_totals['carbs'], 1),
            'fats': round(day_totals['fats'], 1),
            'status': status_for_calories(day_totals['calories']),
        }
        daily_summaries.append(summary)
        chart_data.append({
            'date': date_key,
            'calories': summary['calories'],
            'protein': summary['protein'],
            'carbs': summary['carbs'],
            'fats': summary['fats'],
        })

        if n == 0:
            today_totals = {
                'calories': summary['calories'],
                'protein': summary['protein'],
                'carbs': summary['carbs'],
                'fats': summary['fats'],
            }

    calorie_values = [day['calories'] for day in daily_summaries]
    weekly_average_calories = round(
        sum(calorie_values) / len(calorie_values), 1
    ) if calorie_values else 0

    return render_template(
        'history.html',
        daily_summaries=daily_summaries,
        chart_data=chart_data,
        today_totals=today_totals,
        weekly_average_calories=weekly_average_calories,
        goals=goals
    )


# Run the app
init_database()

if __name__ == '__main__':
    app.run(debug=True)
