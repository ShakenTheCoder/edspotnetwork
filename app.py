import os
import logging
from flask import Flask, redirect, url_for, render_template, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Setup SQLAlchemy with the new style (SQLAlchemy 2.0 compatible)
class Base(DeclarativeBase):
    pass

# Create the db instance
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "edspot-dev-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https
CORS(app)

# Import template filter functions
from feed import time_ago
from messaging import format_time

# Register template filters
app.template_filter('time_ago')(time_ago)
app.template_filter('format_time')(format_time)

# Add context processor for current user in all templates
@app.context_processor
def inject_global_variables():
    from models import User
    
    current_user = None
    if 'user_id' in session:
        current_user = User.query.get(session.get('user_id'))
    
    return {
        'current_user': current_user,
        'current_year': datetime.now().year
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
