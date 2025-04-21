import os
import logging
from flask import Flask, redirect, url_for, render_template
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "edspot-dev-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https
CORS(app)

# Import template filter functions first
from feed import time_ago
from messaging import format_time

# Register template filters
app.template_filter('time_ago')(time_ago)
app.template_filter('format_time')(format_time)

# Import routes after app is created to avoid circular imports
from auth import auth_bp
from feed import feed_bp
from profile import profile_bp
from search import search_bp
from messaging import messaging_bp
from data_store import init_data

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(feed_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(search_bp)
app.register_blueprint(messaging_bp)

# Initialize sample data
init_data()

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
