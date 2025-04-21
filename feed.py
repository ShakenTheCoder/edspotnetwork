from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from models import User, Post
from app import db
from datetime import datetime

feed_bp = Blueprint('feed', __name__)

@feed_bp.route('/home')
@login_required
def home():
    user_id = current_user.id
    user = current_user
    
    # Get posts from people the user is connected with and universities they follow
    # For now, just get all posts ordered by timestamp descending
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    
    # Enrich posts with user information
    enriched_posts = []
    for post in posts:
        post_user = User.query.get(post.user_id)
        if post_user:
            enriched_posts.append({
                'post': post,
                'user': post_user,
                'is_liked': user in post.liked_by
            })
    
    return render_template(
        'feed.html', 
        posts=enriched_posts, 
        user=user
    )

@feed_bp.route('/post', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content')
    
    if not content or len(content.strip()) == 0:
        flash('Post cannot be empty', 'danger')
        return redirect(url_for('feed.home'))
    
    # Create new post
    post = Post(
        user_id=current_user.id,
        content=content
    )
    
    # Add to database
    db.session.add(post)
    db.session.commit()
    
    flash('Post created successfully!', 'success')
    return redirect(url_for('feed.home'))

@feed_bp.route('/post/like/<int:post_id>', methods=['POST'])
@login_required
def like_post_route(post_id):
    post = Post.query.get(post_id)
    
    if not post:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Post not found'}), 404
        flash('Post not found', 'danger')
        return redirect(url_for('feed.home'))
    
    # Add user to liked_by relationship if not already there
    if current_user not in post.liked_by:
        post.liked_by.append(current_user)
        db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'like_count': post.liked_by.count()
        })
    
    return redirect(url_for('feed.home'))

@feed_bp.route('/post/unlike/<int:post_id>', methods=['POST'])
@login_required
def unlike_post_route(post_id):
    post = Post.query.get(post_id)
    
    if not post:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Post not found'}), 404
        flash('Post not found', 'danger')
        return redirect(url_for('feed.home'))
    
    # Remove user from liked_by relationship if present
    if current_user in post.liked_by:
        post.liked_by.remove(current_user)
        db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'like_count': post.liked_by.count()
        })
    
    return redirect(url_for('feed.home'))

# This will be registered with the app in app.py
def time_ago(dt):
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime("%b %d, %Y")
