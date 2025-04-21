from datetime import datetime, timedelta
import random
from models import User, Post, Message, ChatMessage

# In-memory data stores
users = {}
posts = {}
messages = {}
chat_messages = []
next_user_id = 1
next_post_id = 1
next_message_id = 1
next_chat_message_id = 1

def get_next_user_id():
    global next_user_id
    current_id = next_user_id
    next_user_id += 1
    return current_id

def get_next_post_id():
    global next_post_id
    current_id = next_post_id
    next_post_id += 1
    return current_id

def get_next_message_id():
    global next_message_id
    current_id = next_message_id
    next_message_id += 1
    return current_id

def get_next_chat_message_id():
    global next_chat_message_id
    current_id = next_chat_message_id
    next_chat_message_id += 1
    return current_id

def add_user(email, password, user_type, name=None, profile_image=None):
    user_id = get_next_user_id()
    user = User(user_id, email, password, user_type, name, profile_image)
    users[user_id] = user
    return user

def get_user_by_id(user_id):
    return users.get(user_id)

def get_user_by_email(email):
    for user in users.values():
        if user.email.lower() == email.lower():
            return user
    return None

def update_user(user):
    if user.id in users:
        users[user.id] = user
        return True
    return False

def add_post(user_id, content):
    post_id = get_next_post_id()
    post = Post(post_id, user_id, content)
    posts[post_id] = post
    return post

def get_post_by_id(post_id):
    return posts.get(post_id)

def get_posts_by_user(user_id):
    return [post for post in posts.values() if post.user_id == user_id]

def get_feed_for_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return []
    
    if user.user_type == 'student':
        # Get posts from connected students and followed universities
        feed_posts = []
        for post_id, post in posts.items():
            post_user = get_user_by_id(post.user_id)
            if not post_user:
                continue
                
            if post_user.user_type == 'student' and post_user.id in user.connections:
                feed_posts.append(post)
            elif post_user.user_type == 'university' and post_user.id in user.followed_universities:
                feed_posts.append(post)
                
        # Sort by timestamp, newest first
        feed_posts.sort(key=lambda p: p.timestamp, reverse=True)
        return feed_posts
    else:  # university
        # Universities see posts from their followers
        feed_posts = []
        for post_id, post in posts.items():
            post_user = get_user_by_id(post.user_id)
            if post_user and post_user.id in user.followers:
                feed_posts.append(post)
                
        feed_posts.sort(key=lambda p: p.timestamp, reverse=True)
        return feed_posts

def like_post(post_id, user_id):
    post = get_post_by_id(post_id)
    if not post:
        return False
    
    if user_id not in post.likes:
        post.likes.append(user_id)
    return True

def unlike_post(post_id, user_id):
    post = get_post_by_id(post_id)
    if not post:
        return False
    
    if user_id in post.likes:
        post.likes.remove(user_id)
    return True

def add_message(sender_id, receiver_id, content):
    message_id = get_next_message_id()
    message = Message(message_id, sender_id, receiver_id, content)
    
    if sender_id not in messages:
        messages[sender_id] = {}
    if receiver_id not in messages[sender_id]:
        messages[sender_id][receiver_id] = []
    
    messages[sender_id][receiver_id].append(message)
    
    # Also add to receiver's inbox
    if receiver_id not in messages:
        messages[receiver_id] = {}
    if sender_id not in messages[receiver_id]:
        messages[receiver_id][sender_id] = []
    
    messages[receiver_id][sender_id].append(message)
    
    return message

def get_conversation(user1_id, user2_id):
    conversation = []
    
    if user1_id in messages and user2_id in messages[user1_id]:
        conversation.extend(messages[user1_id][user2_id])
    
    # Sort by timestamp
    conversation.sort(key=lambda m: m.timestamp)
    
    return conversation

def get_conversations(user_id):
    if user_id not in messages:
        return []
    
    conversations = []
    for other_user_id in messages[user_id]:
        # Get the most recent message for each conversation
        msgs = messages[user_id][other_user_id]
        if msgs:
            # Sort by timestamp, newest first
            sorted_msgs = sorted(msgs, key=lambda m: m.timestamp, reverse=True)
            other_user = get_user_by_id(other_user_id)
            if other_user:
                conversations.append({
                    'user': other_user,
                    'last_message': sorted_msgs[0]
                })
    
    # Sort conversations by the timestamp of the last message, newest first
    conversations.sort(key=lambda c: c['last_message'].timestamp, reverse=True)
    
    return conversations

def add_chat_message(user_id, content):
    chat_id = get_next_chat_message_id()
    chat_message = ChatMessage(chat_id, user_id, content)
    chat_messages.append(chat_message)
    
    # Limit to last 100 messages
    if len(chat_messages) > 100:
        chat_messages.pop(0)
    
    return chat_message

def get_chat_messages(limit=50):
    return sorted(chat_messages, key=lambda m: m.timestamp)[-limit:]

def search_users(query, user_type=None, location=None, skills=None, programs=None):
    results = []
    if query:
        query = query.lower()
    
    for user in users.values():
        # Filter by user type
        if user_type and user.user_type != user_type:
            continue
            
        # Initialize match flags
        query_match = True
        location_match = True
        skills_match = True
        programs_match = True
        
        # Filter by query (name, email, bio/description)
        if query:
            query_match = (
                query in user.name.lower() or 
                query in user.email.lower() or 
                (user.user_type == 'student' and hasattr(user, 'bio') and query in user.bio.lower()) or
                (user.user_type == 'university' and hasattr(user, 'description') and query in user.description.lower())
            )
        
        # Filter by location
        if location and location.strip():
            location = location.lower().strip()
            if user.user_type == 'student':
                # For students, check education which might contain location info
                location_match = any(location in edu.lower() for edu in user.education if edu)
            else:
                # For universities, check the location attribute
                location_match = location in getattr(user, 'location', '').lower()
        
        # Filter by skills (for students)
        if skills and skills.strip() and user.user_type == 'student':
            skills_list = [s.strip().lower() for s in skills.split(',') if s.strip()]
            skills_match = any(skill in ' '.join(user.skills).lower() for skill in skills_list)
        
        # Filter by programs (for universities)
        if programs and programs.strip() and user.user_type == 'university':
            programs_list = [p.strip().lower() for p in programs.split(',') if p.strip()]
            # Assume description might contain program information
            programs_match = any(program in getattr(user, 'description', '').lower() for program in programs_list)
        
        # Add to results if all criteria match
        if query_match and location_match and skills_match and programs_match:
            results.append(user)
    
    return results

def connect_users(user1_id, user2_id):
    user1 = get_user_by_id(user1_id)
    user2 = get_user_by_id(user2_id)
    
    if not user1 or not user2:
        return False
        
    if user1.user_type != 'student' or user2.user_type != 'student':
        return False
        
    if user2_id not in user1.connections:
        user1.connections.append(user2_id)
        
    if user1_id not in user2.connections:
        user2.connections.append(user1_id)
        
    return True

def follow_university(student_id, university_id):
    student = get_user_by_id(student_id)
    university = get_user_by_id(university_id)
    
    if not student or not university:
        return False
        
    if student.user_type != 'student' or university.user_type != 'university':
        return False
        
    if university_id not in student.followed_universities:
        student.followed_universities = getattr(student, 'followed_universities', [])
        student.followed_universities.append(university_id)
        
    if student_id not in university.followers:
        university.followers.append(student_id)
        
    return True

def init_data():
    """Initialize some sample data for the platform"""
    # Clear existing data
    global users, posts, messages, chat_messages, add_user
    users = {}
    posts = {}
    messages = {}
    chat_messages = []
    
    # Add the followed_universities attribute to student users
    original_add_user = add_user
    
    def modified_add_user(email, password, user_type, name=None, profile_image=None):
        user = original_add_user(email, password, user_type, name, profile_image)
        if user.user_type == 'student':
            user.followed_universities = []
        return user
    
    add_user = modified_add_user
