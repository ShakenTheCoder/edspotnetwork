from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from database import db
import json

# Many-to-many relationships tables
student_connections = Table(
    'student_connections',
    db.metadata,
    Column('student1_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('student2_id', Integer, ForeignKey('user.id'), primary_key=True)
)

student_university = Table(
    'student_university',
    db.metadata,
    Column('student_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('university_id', Integer, ForeignKey('user.id'), primary_key=True)
)

post_likes = Table(
    'post_likes',
    db.metadata,
    Column('post_id', Integer, ForeignKey('post.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    user_type = Column(String(20), nullable=False)  # 'student' or 'university'
    name = Column(String(100))
    profile_image = Column(String(200))
    date_joined = Column(DateTime, default=datetime.now)
    
    # For students
    bio = Column(Text, default="")
    education = Column(Text, default="[]")  # JSON-encoded list
    skills = Column(Text, default="[]")  # JSON-encoded list
    
    # For universities
    description = Column(Text, default="")
    location = Column(String(100), default="")
    website = Column(String(100), default="")
    
    # Relationships
    posts = relationship("Post", backref="author", lazy=True, cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", backref="sender", lazy=True, cascade="all, delete-orphan")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", backref="receiver", lazy=True, cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", backref="user", lazy=True, cascade="all, delete-orphan")
    
    # Use hybrid properties for serialized arrays
    @property
    def education_list(self):
        return json.loads(self.education) if self.education else []
    
    @education_list.setter
    def education_list(self, education_list):
        self.education = json.dumps(education_list)
    
    @property
    def skills_list(self):
        return json.loads(self.skills) if self.skills else []
    
    @skills_list.setter
    def skills_list(self, skills_list):
        self.skills = json.dumps(skills_list)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
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
                'education': self.education_list,
                'skills': self.skills_list,
                # These would be fetched from the relationships via queries
                'connections': [],
                'followed_universities': []
            })
        else:  # university
            base_dict.update({
                'description': self.description,
                'location': self.location,
                'website': self.website,
                # These would be fetched from the relationships via queries
                'followers': []
            })
            
        return base_dict


class Post(db.Model):
    __tablename__ = 'post'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    
    # Many-to-many relationship for likes
    liked_by = relationship('User', secondary=post_likes, lazy='dynamic',
                           backref=db.backref('liked_posts', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'timestamp': self.timestamp,
            'likes': [user.id for user in self.liked_by],
            'like_count': self.liked_by.count()
        }


class Message(db.Model):
    __tablename__ = 'message'
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    is_read = Column(Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'timestamp': self.timestamp,
            'is_read': self.is_read
        }


class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'timestamp': self.timestamp
        }
