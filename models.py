from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, id, email, password, user_type, name=None, profile_image=None):
        self.id = id
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.user_type = user_type  # 'student' or 'university'
        self.name = name
        self.profile_image = profile_image
        self.date_joined = datetime.now()
        
        # For students
        self.bio = ""
        self.education = []
        self.skills = []
        self.connections = []  # IDs of connected students
        self.followed_universities = []  # IDs of universities the student follows
        
        # For universities
        self.description = ""
        self.location = ""
        self.website = ""
        self.followers = []  # IDs of interested students
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        base_dict = {
            'id': self.id,
            'email': self.email,
            'user_type': self.user_type,
            'name': self.name,
            'profile_image': self.profile_image,
            'date_joined': self.date_joined
        }
        
        if self.user_type == 'student':
            base_dict.update({
                'bio': self.bio,
                'education': self.education,
                'skills': self.skills,
                'connections': self.connections,
                'followed_universities': self.followed_universities
            })
        else:  # university
            base_dict.update({
                'description': self.description,
                'location': self.location,
                'website': self.website,
                'followers': self.followers
            })
            
        return base_dict

class Post:
    def __init__(self, id, user_id, content, timestamp=None):
        self.id = id
        self.user_id = user_id
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.likes = []  # List of user IDs who liked the post
        
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'timestamp': self.timestamp,
            'likes': self.likes,
            'like_count': len(self.likes)
        }

class Message:
    def __init__(self, id, sender_id, receiver_id, content, timestamp=None):
        self.id = id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.is_read = False
        
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'timestamp': self.timestamp,
            'is_read': self.is_read
        }

class ChatMessage:
    def __init__(self, id, user_id, content, timestamp=None):
        self.id = id
        self.user_id = user_id
        self.content = content
        self.timestamp = timestamp or datetime.now()
        
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'timestamp': self.timestamp
        }
