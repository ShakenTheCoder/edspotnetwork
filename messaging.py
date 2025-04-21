from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from models import User, Message, ChatMessage
from app import db
from sqlalchemy import or_, and_
from datetime import datetime

messaging_bp = Blueprint('messaging', __name__)

@messaging_bp.route('/messages')
@login_required
def messages():
    user_id = current_user.id
    
    # Get all conversations where current user is either sender or receiver
    sent_messages = Message.query.filter_by(sender_id=user_id).all()
    received_messages = Message.query.filter_by(receiver_id=user_id).all()
    
    # Extract unique conversation partners
    conversation_partners = set()
    for msg in sent_messages:
        conversation_partners.add(msg.receiver_id)
    for msg in received_messages:
        conversation_partners.add(msg.sender_id)
    
    # Build conversation list
    conversations = []
    for partner_id in conversation_partners:
        partner = User.query.get(partner_id)
        if partner:
            # Get the most recent message
            last_message = Message.query.filter(
                or_(
                    and_(Message.sender_id == user_id, Message.receiver_id == partner_id),
                    and_(Message.sender_id == partner_id, Message.receiver_id == user_id)
                )
            ).order_by(Message.timestamp.desc()).first()
            
            # Count unread messages
            unread_count = Message.query.filter_by(
                sender_id=partner_id,
                receiver_id=user_id,
                is_read=False
            ).count()
            
            conversations.append({
                'user': partner,
                'last_message': last_message,
                'unread_count': unread_count
            })
    
    # Sort conversations by last message timestamp
    conversations.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else datetime.min, reverse=True)
    
    return render_template('messages.html', conversations=conversations)

@messaging_bp.route('/messages/<int:other_user_id>', methods=['GET', 'POST'])
@login_required
def conversation(other_user_id):
    user_id = current_user.id
    other_user = User.query.get(other_user_id)
    
    if not other_user:
        flash('User not found', 'danger')
        return redirect(url_for('messaging.messages'))
    
    if request.method == 'POST':
        content = request.form.get('message')
        
        if content and not Message.query.filter(
            Message.sender_id == user_id,
            Message.receiver_id == other_user_id,
            Message.content == content,
            Message.timestamp >= datetime.now() - timedelta(seconds=5)
        ).first():
            # Create new message only if no duplicate exists within last 5 seconds
            message = Message(
                sender_id=user_id,
                receiver_id=other_user_id,
                content=content
            )
            
            # Save to database
            db.session.add(message)
            db.session.commit()
            
            # Always return JSON response
            return jsonify({
                'status': 'success',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_sender': True
                }
            })
        return jsonify({'status': 'error', 'message': 'Duplicate message'})
    
    # Get messages between the two users
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
        )
    ).order_by(Message.timestamp).all()
    
    # Mark received messages as read
    for msg in messages:
        if msg.receiver_id == user_id and not msg.is_read:
            msg.is_read = True
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        since_id = request.args.get('since', 0, type=int)
        filtered_messages = [msg for msg in messages if msg.id > since_id]
        return jsonify({
            'messages': [
                {
                    'id': msg.id,
                    'content': msg.content,
                    'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_sender': msg.sender_id == user_id
                } for msg in filtered_messages
            ]
        })
    
    # Get conversations for sidebar
    # We reuse the code from the messages route, this would normally be refactored
    # to a helper function to avoid duplication
    sent_messages = Message.query.filter_by(sender_id=user_id).all()
    received_messages = Message.query.filter_by(receiver_id=user_id).all()
    
    conversation_partners = set()
    for msg in sent_messages:
        conversation_partners.add(msg.receiver_id)
    for msg in received_messages:
        conversation_partners.add(msg.sender_id)
    
    conversations = []
    for partner_id in conversation_partners:
        partner = User.query.get(partner_id)
        if partner:
            last_message = Message.query.filter(
                or_(
                    and_(Message.sender_id == user_id, Message.receiver_id == partner_id),
                    and_(Message.sender_id == partner_id, Message.receiver_id == user_id)
                )
            ).order_by(Message.timestamp.desc()).first()
            
            unread_count = Message.query.filter_by(
                sender_id=partner_id,
                receiver_id=user_id,
                is_read=False
            ).count()
            
            conversations.append({
                'user': partner,
                'last_message': last_message,
                'unread_count': unread_count
            })
    
    conversations.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else datetime.min, reverse=True)
    
    return render_template(
        'messages.html',
        other_user=other_user,
        messages=messages,
        conversations=conversations
    )

@messaging_bp.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    # Handle message posting
    if request.method == 'POST':
        content = request.form.get('message')
        
        if content:
            # Create new chat message
            message = ChatMessage(
                user_id=current_user.id,
                content=content
            )
            
            # Save to database
            db.session.add(message)
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'success',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'user': {
                            'id': current_user.id,
                            'name': current_user.name,
                            'user_type': current_user.user_type
                        }
                    }
                })
    
    # Check if we're polling for new messages since a specific ID
    since_id = request.args.get('since', 0, type=int)
    
    # Get chat messages
    query = ChatMessage.query.order_by(ChatMessage.timestamp)
    
    # Filter messages if since_id is provided in AJAX request
    if since_id > 0:
        query = query.filter(ChatMessage.id > since_id)
    
    messages = query.all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response_messages = []
        for msg in messages:
            sender = User.query.get(msg.user_id)
            if sender:
                response_messages.append({
                    'id': msg.id,
                    'content': msg.content,
                    'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'user': {
                        'id': sender.id,
                        'name': sender.name,
                        'user_type': sender.user_type
                    }
                })
        
        return jsonify({
            'messages': response_messages
        })
    
    # For regular page load, get all messages with their related users and avoid duplicates
    # Use distinct on id to ensure each message appears only once
    messages = ChatMessage.query.order_by(ChatMessage.timestamp).all()
    
    # Use a set to track message IDs to prevent duplicates
    seen_message_ids = set()
    unique_messages = []
    
    # Filter out duplicate messages
    for message in messages:
        if message.id not in seen_message_ids:
            # Load the user relationship
            message.user = User.query.get(message.user_id)
            unique_messages.append(message)
            seen_message_ids.add(message.id)
    
    return render_template('chat.html', messages=unique_messages)

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
