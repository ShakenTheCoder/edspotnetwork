from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from data_store import add_post, get_feed_for_user, get_user_by_id, like_post, unlike_post
from auth import login_required
from datetime import datetime

feed_bp = Blueprint('feed', __name__)

@feed_bp.route('/home')
@login_required
def home():
    user_id = session.get('user_id')
    user = get_user_by_id(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('auth.logout'))
    
    posts = get_feed_for_user(user_id)
    
    # Enrich posts with user information
    enriched_posts = []
    for post in posts:
        post_user = get_user_by_id(post.user_id)
        if post_user:
            enriched_posts.append({
                'post': post,
                'user': post_user,
                'is_liked': user_id in post.likes
            })
    
    return render_template(
        'feed.html', 
        posts=enriched_posts, 
        user=user
    )

@feed_bp.route('/post', methods=['POST'])
@login_required
def create_post():
    user_id = session.get('user_id')
    content = request.form.get('content')
    
    if not content or len(content.strip()) == 0:
        flash('Post cannot be empty', 'danger')
        return redirect(url_for('feed.home'))
    
    post = add_post(user_id, content)
    flash('Post created successfully!', 'success')
    
    return redirect(url_for('feed.home'))

@feed_bp.route('/post/like/<int:post_id>', methods=['POST'])
@login_required
def like_post_route(post_id):
    user_id = session.get('user_id')
    success = like_post(post_id, user_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if success:
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Post not found'}), 404
    
    return redirect(url_for('feed.home'))

@feed_bp.route('/post/unlike/<int:post_id>', methods=['POST'])
@login_required
def unlike_post_route(post_id):
    user_id = session.get('user_id')
    success = unlike_post(post_id, user_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if success:
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Post not found'}), 404
    
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
