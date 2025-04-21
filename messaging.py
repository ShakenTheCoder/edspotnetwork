from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from data_store import get_user_by_id, add_message, get_conversation, get_conversations, add_chat_message, get_chat_messages
from auth import login_required
from datetime import datetime

messaging_bp = Blueprint('messaging', __name__)

@messaging_bp.route('/messages')
@login_required
def messages():
    user_id = session.get('user_id')
    conversations = get_conversations(user_id)
    
    return render_template('messages.html', conversations=conversations)

@messaging_bp.route('/messages/<int:other_user_id>', methods=['GET', 'POST'])
@login_required
def conversation(other_user_id):
    user_id = session.get('user_id')
    other_user = get_user_by_id(other_user_id)
    
    if not other_user:
        flash('User not found', 'danger')
        return redirect(url_for('messaging.messages'))
    
    if request.method == 'POST':
        content = request.form.get('message')
        
        if content:
            message = add_message(user_id, other_user_id, content)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'success',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'is_sender': True
                    }
                })
    
    messages = get_conversation(user_id, other_user_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'messages': [
                {
                    'id': msg.id,
                    'content': msg.content,
                    'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_sender': msg.sender_id == user_id
                } for msg in messages
            ]
        })
    
    return render_template(
        'messages.html',
        other_user=other_user,
        messages=messages,
        conversations=get_conversations(user_id)
    )

@messaging_bp.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    user_id = session.get('user_id')
    user = get_user_by_id(user_id)
    
    if request.method == 'POST':
        content = request.form.get('message')
        
        if content:
            message = add_chat_message(user_id, content)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                sender = get_user_by_id(message.user_id)
                return jsonify({
                    'status': 'success',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'user': {
                            'id': sender.id if sender else 0,
                            'name': sender.name if sender else "Unknown User",
                            'user_type': sender.user_type if sender else "unknown"
                        }
                    }
                })
    
    messages = get_chat_messages()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'messages': [
                {
                    'id': msg.id,
                    'content': msg.content,
                    'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'user': {
                        'id': get_user_by_id(msg.user_id).id if get_user_by_id(msg.user_id) else 0,
                        'name': get_user_by_id(msg.user_id).name if get_user_by_id(msg.user_id) else "Unknown User",
                        'user_type': get_user_by_id(msg.user_id).user_type if get_user_by_id(msg.user_id) else "unknown"
                    }
                } for msg in messages if get_user_by_id(msg.user_id)
            ]
        })
    
    return render_template('chat.html', messages=messages)

# This will be registered with the app in app.py
def format_time(dt):
    now = datetime.now()
    diff = now - dt
    
    if diff.days == 0:
        return dt.strftime('%I:%M %p')
    elif diff.days < 7:
        return dt.strftime('%a %I:%M %p')
    else:
        return dt.strftime('%b %d, %Y')
