from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from data_store import add_user, get_user_by_email, get_user_by_id
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        user = get_user_by_id(session['user_id'])
        if not user or user.user_type != 'student':
            flash('This page is only accessible to students', 'warning')
            return redirect(url_for('feed.home'))
        
        return f(*args, **kwargs)
    return decorated_function

def university_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        user = get_user_by_id(session['user_id'])
        if not user or user.user_type != 'university':
            flash('This page is only accessible to universities', 'warning')
            return redirect(url_for('feed.home'))
        
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        user_type = request.form.get('user_type')
        
        # Validation
        error = None
        if not email or not password or not confirm_password or not name or not user_type:
            error = 'All fields are required'
        elif password != confirm_password:
            error = 'Passwords do not match'
        elif get_user_by_email(email):
            error = f'Email {email} is already registered'
        elif user_type not in ['student', 'university']:
            error = 'Invalid account type'
        
        if error:
            flash(error, 'danger')
        else:
            user = add_user(email, password, user_type, name)
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = get_user_by_email(email)
        
        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            
            next_page = request.args.get('next')
            if not next_page or next_page.startswith('/'):
                next_page = url_for('feed.home')
                
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page)
        
        flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.context_processor
def inject_user():
    if 'user_id' in session:
        return {'current_user': get_user_by_id(session['user_id'])}
    return {'current_user': None}
