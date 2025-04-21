import re
from functools import wraps
from flask import flash, redirect, url_for, session, request
from data_store import get_user_by_id

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_current_user():
    """Get the current logged-in user"""
    if 'user_id' in session:
        return get_user_by_id(session['user_id'])
    return None

def get_unread_message_count(user_id):
    """Get the count of unread messages for a user"""
    # This would interact with the data store to count unread messages
    # For now, we'll just return a placeholder value
    return 0
