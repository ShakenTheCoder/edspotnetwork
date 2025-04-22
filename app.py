import os
import logging
from flask import Flask, redirect, url_for, render_template, session
from flask_cors import CORS
from flask_login import LoginManager, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
from database import db
from utils import get_unread_message_count

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create login manager
login_manager = LoginManager()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "edspot-dev-key")
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https
CORS(app)

# Import template filter functions
from feed import time_ago
from messaging import format_time

# Register template filters
app.template_filter('time_ago')(time_ago)
app.template_filter('format_time')(format_time)

# Setup Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Add context processor for current user in all templates
@app.context_processor
def inject_global_variables():
    return {
        'current_user': current_user,
        'current_year': datetime.now().year,
        'get_unread_message_count': get_unread_message_count
    }

# Create db tables within app context
with app.app_context():
    # Import models to create tables
    import models
    db.create_all()

# Import routes after app is created to avoid circular imports
from auth import auth_bp
from feed import feed_bp
from profile import profile_bp
from search import search_bp
from messaging import messaging_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(feed_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(search_bp)
app.register_blueprint(messaging_bp)

# Root route redirects to feed
@app.route('/')
def index():
    return redirect(url_for('feed.home'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Page Not Found", message="The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error="Server Error", message="An unexpected error occurred. Please try again later."), 500
