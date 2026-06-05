from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection
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
    Displays the user dashboard.
    Protected route that requires user to be logged in.
    Returns: render_template of dashboard.html
    """
    return render_template('dashboard.html', username=current_user.username)


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
