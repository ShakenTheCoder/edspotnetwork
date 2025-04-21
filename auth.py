from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from functools import wraps
from models import User
from app import db
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__)

def login_required_custom(f):
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
        
        user = User.query.get(session['user_id'])
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
        
        user = User.query.get(session['user_id'])
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
        elif User.query.filter_by(email=email).first():
            error = f'Email {email} is already registered'
        elif user_type not in ['student', 'university']:
            error = 'Invalid account type'
        
        if error:
            flash(error, 'danger')
        else:
            # Create new user
            new_user = User(
                email=email,
                user_type=user_type,
                name=name
            )
            new_user.set_password(password)
            
            # Add to database
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Clear session and set user_id
            session.clear()
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            
            # Use Flask-Login to login the user (optional)
            login_user(user)
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('feed.home')
                
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page)
        
        flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    # Clear session
    session.clear()
    
    # Use Flask-Login to logout (optional)
    logout_user()
    
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.context_processor
def inject_user():
    if 'user_id' in session:
        return {'current_user': User.query.get(session['user_id'])}
    return {'current_user': None}
