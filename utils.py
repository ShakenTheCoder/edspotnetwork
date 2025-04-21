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
    """Get the count of unread messages for a user
    
    Args:
        user_id: The ID of the user to check unread messages for
        
    Returns:
        int: Number of unread messages
    """
    from models import Message
    from sqlalchemy import and_
    from app import db
    
    try:
        # Use efficient count query
        unread_count = db.session.query(Message).filter(
            and_(
                Message.receiver_id == user_id,
                Message.is_read.is_(False)  # More explicit than == False
            )
        ).count()
        
        return unread_count
    except Exception as e:
        print(f"Error getting unread message count: {e}")
        return 0
