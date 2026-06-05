from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection
from datetime import date
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

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
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate input
        if not username or not email or not password:
            flash('Please fill in all fields.', 'danger')
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
            flash('Registration successful! Please log in.', 'success')
            connection.close()
            return redirect(url_for('login'))
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
        SELECT fl.id, f.name, fl.quantity_grams, fl.meal_type, f.calories_per_100g, f.protein, f.carbs, f.fats
        FROM food_log fl
        JOIN foods f ON fl.food_id = f.id
        WHERE fl.user_id = ? AND fl.logged_date = ?
        ORDER BY fl.id DESC
    ''', (current_user.id, today))
    today_foods = cursor.fetchall()

    # Calculate daily totals
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fats = 0
    today_food_list = []

    for food in today_foods:
        multiplier = food['quantity_grams'] / 100
        calories = food['calories_per_100g'] * multiplier
        protein = food['protein'] * multiplier
        carbs = food['carbs'] * multiplier
        fats = food['fats'] * multiplier

        total_calories += calories
        total_protein += protein
        total_carbs += carbs
        total_fats += fats

        today_food_list.append({
            'id': food['id'],
            'name': food['name'],
            'quantity_grams': food['quantity_grams'],
            'meal_type': food['meal_type'],
            'calories': round(calories, 1)
        })

    # Query user goals
    cursor.execute('SELECT daily_calories, daily_protein, daily_carbs, daily_fats FROM goals WHERE user_id = ?', (current_user.id,))
    goals_row = cursor.fetchone()
    connection.close()

    # Use default goals if not set
    if goals_row:
        goals = {
            'daily_calories': goals_row['daily_calories'],
            'daily_protein': goals_row['daily_protein'],
            'daily_carbs': goals_row['daily_carbs'],
            'daily_fats': goals_row['daily_fats']
        }
    else:
        goals = {
            'daily_calories': 2000,
            'daily_protein': 150,
            'daily_carbs': 250,
            'daily_fats': 65
        }

    # Calculate percentages (capped at 100%)
    progress = {
        'calories': min(int((total_calories / goals['daily_calories']) * 100), 100),
        'protein': min(int((total_protein / goals['daily_protein']) * 100), 100),
        'carbs': min(int((total_carbs / goals['daily_carbs']) * 100), 100),
        'fats': min(int((total_fats / goals['daily_fats']) * 100), 100)
    }

    return render_template('dashboard.html',
                         username=current_user.username,
                         total_calories=round(total_calories, 1),
                         total_protein=round(total_protein, 1),
                         total_carbs=round(total_carbs, 1),
                         total_fats=round(total_fats, 1),
                         goals=goals,
                         progress=progress,
                         today_foods=today_food_list)


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
            ''', (current_user.id, food_id, quantity_grams, meal_type, date.today()))
            connection.commit()
            flash(f'Food logged successfully! ({nutrition["calories"]:.1f} kcal)', 'success')
            connection.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Failed to log food: {str(e)}', 'danger')
            connection.close()
            return redirect(url_for('log_food'))

    # GET request: fetch all foods
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT id, name FROM foods ORDER BY name')
    foods = cursor.fetchall()
    connection.close()

    return render_template('log_food.html', foods=foods)


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


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
