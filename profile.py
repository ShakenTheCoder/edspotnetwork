from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, Post
from app import db
from werkzeug.security import generate_password_hash
from sqlalchemy import and_, or_

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def my_profile():
    """Route for viewing the current user's own profile"""
    return redirect(url_for('profile.view_profile', user_id=current_user.id))

@profile_bp.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    """View a user's profile by user ID"""
    # If this is current user, use current_user directly
    if current_user.id == user_id:
        user = current_user
    else:
        user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('feed.home'))
    
    # Get user's posts
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.timestamp.desc()).all()
    
    if user.user_type == 'student':
        # Check if users are connected
        # For now, we'll just set a placeholder since we need to implement the many-to-many relationship properly
        is_connected = False
        
        # Get education and skills from JSON fields
        education = user.education_list  # Using our property
        skills = user.skills_list
        
        return render_template(
            'student_profile.html',
            user=user,
            posts=posts,
            is_connected=is_connected,
            education=education,
            skills=skills,
            is_self=(current_user.id == user_id)
        )
    else:  # university
        # Check if current user is following this university
        is_following = False
        
        # In a real implementation, we'd query the student_university join table
        # For now, this is a placeholder
        
        return render_template(
            'university_profile.html',
            university=user,
            posts=posts,
            is_following=is_following,
            is_self=(current_user.id == user_id)
        )

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Use current_user from Flask-Login
    user = current_user
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        # Common validation
        if not name or not email:
            flash('Name and email are required', 'danger')
            return redirect(url_for('profile.edit_profile'))
        
        user.name = name
        user.email = email
        
        # Handle password change if provided
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password:
            if not user.check_password(current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('profile.edit_profile'))
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'danger')
                return redirect(url_for('profile.edit_profile'))
            
            # Update password
            user.password_hash = generate_password_hash(new_password)
        
        # Type-specific fields
        if user.user_type == 'student':
            bio = request.form.get('bio')
            education_raw = request.form.get('education')
            skills_raw = request.form.get('skills')
            
            user.bio = bio
            
            # Process education (comma-separated list)
            if education_raw:
                user.education_list = [e.strip() for e in education_raw.split(',') if e.strip()]
            
            # Process skills (comma-separated list)
            if skills_raw:
                user.skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]
                
        else:  # university
            description = request.form.get('description')
            location = request.form.get('location')
            website = request.form.get('website')
            
            user.description = description
            user.location = location
            user.website = website
        
        # Save changes to database
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.view_profile', user_id=user.id))
    
    return render_template('edit_profile.html', user=user)

@profile_bp.route('/connect/<int:user_id>', methods=['POST'])
@login_required
def connect_with_user(user_id):
    # Check if current user is a student
    if current_user.user_type != 'student':
        flash('Only students can connect with other users', 'warning')
        return redirect(url_for('feed.home'))
    
    target_user = User.query.get(user_id)
    
    if not target_user:
        flash('User not found', 'danger')
        return redirect(url_for('feed.home'))
    
    if target_user.user_type != 'student':
        flash('You can only connect with other students', 'warning')
        return redirect(url_for('profile.view_profile', user_id=user_id))
    
    if user_id == current_user.id:
        flash('You cannot connect with yourself', 'warning')
        return redirect(url_for('profile.view_profile', user_id=user_id))
    
    # For now we'll implement this with a simple approach
    # In a real implementation, we would use a many-to-many relationship table
    
    # Create connection in database
    # This is just a placeholder for now
    flash(f'You are now connected with {target_user.name}!', 'success')
    return redirect(url_for('profile.view_profile', user_id=user_id))

@profile_bp.route('/follow/<int:university_id>', methods=['POST'])
@login_required
def follow_university(university_id):
    # Check if current user is a student
    if current_user.user_type != 'student':
        flash('Only students can follow universities', 'warning')
        return redirect(url_for('feed.home'))
    
    university = User.query.get(university_id)
    
    if not university:
        flash('University not found', 'danger')
        return redirect(url_for('feed.home'))
    
    if university.user_type != 'university':
        flash('You can only follow universities', 'warning')
        return redirect(url_for('profile.view_profile', user_id=university_id))
    
    # This is a placeholder implementation
    # In a full implementation, we would use a many-to-many relationship table
    # to track student-university following relationships
    
    flash(f'You are now following {university.name}!', 'success')
    return redirect(url_for('profile.view_profile', user_id=university_id))

@profile_bp.route('/unfollow/<int:university_id>', methods=['POST'])
@login_required
def unfollow_university(university_id):
    # Check if current user is a student
    if current_user.user_type != 'student':
        flash('Only students can unfollow universities', 'warning')
        return redirect(url_for('feed.home'))
    
    university = User.query.get(university_id)
    
    if not university:
        flash('University not found', 'danger')
        return redirect(url_for('feed.home'))
    
    # This is a placeholder implementation
    # In a full implementation, we would remove the relationship from a many-to-many table
    
    flash(f'You have unfollowed {university.name}', 'info')
    return redirect(url_for('profile.view_profile', user_id=university_id))

@profile_bp.route('/disconnect/<int:user_id>', methods=['POST'])
@login_required
def disconnect_from_user(user_id):
    # Check if current user is a student
    if current_user.user_type != 'student':
        flash('Only students can disconnect from users', 'warning')
        return redirect(url_for('feed.home'))
    
    target_user = User.query.get(user_id)
    
    if not target_user:
        flash('User not found', 'danger')
        return redirect(url_for('feed.home'))
    
    # This is a placeholder implementation
    # In a full implementation, we would remove the connection from a many-to-many table
    
    flash(f'You are no longer connected with {target_user.name}', 'info')
    return redirect(url_for('profile.view_profile', user_id=user_id))
