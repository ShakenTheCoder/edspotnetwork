from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from data_store import get_user_by_id, update_user, get_posts_by_user
from auth import login_required, student_required, university_required
from werkzeug.security import generate_password_hash

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = get_user_by_id(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('feed.home'))
    
    posts = get_posts_by_user(user_id)
    current_user_id = session.get('user_id')
    current_user = get_user_by_id(current_user_id)
    
    if user.user_type == 'student':
        # Check if users are connected
        is_connected = current_user_id in user.connections
        # Get education and skills
        education = user.education
        skills = user.skills
        
        return render_template(
            'student_profile.html',
            user=user,
            posts=posts,
            is_connected=is_connected,
            education=education,
            skills=skills,
            is_self=(current_user_id == user_id)
        )
    else:  # university
        # Check if current user is following this university
        is_following = False
        if current_user and current_user.user_type == 'student':
            is_following = user.id in getattr(current_user, 'followed_universities', [])
        
        return render_template(
            'university_profile.html',
            university=user,
            posts=posts,
            is_following=is_following,
            is_self=(current_user_id == user_id)
        )

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_id = session.get('user_id')
    user = get_user_by_id(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('auth.logout'))
    
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
                user.education = [e.strip() for e in education_raw.split(',') if e.strip()]
            
            # Process skills (comma-separated list)
            if skills_raw:
                user.skills = [s.strip() for s in skills_raw.split(',') if s.strip()]
                
        else:  # university
            description = request.form.get('description')
            location = request.form.get('location')
            website = request.form.get('website')
            
            user.description = description
            user.location = location
            user.website = website
        
        update_success = update_user(user)
        
        if update_success:
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.view_profile', user_id=user_id))
        else:
            flash('Failed to update profile', 'danger')
    
    return render_template('edit_profile.html', user=user)

@profile_bp.route('/connect/<int:user_id>', methods=['POST'])
@student_required
def connect_with_user(user_id):
    current_user_id = session.get('user_id')
    current_user = get_user_by_id(current_user_id)
    target_user = get_user_by_id(user_id)
    
    if not target_user:
        flash('User not found', 'danger')
        return redirect(url_for('feed.home'))
    
    if target_user.user_type != 'student':
        flash('You can only connect with other students', 'warning')
        return redirect(url_for('profile.view_profile', user_id=user_id))
    
    if user_id == current_user_id:
        flash('You cannot connect with yourself', 'warning')
        return redirect(url_for('profile.view_profile', user_id=user_id))
    
    # Add to connections
    if user_id not in current_user.connections:
        current_user.connections.append(user_id)
        update_user(current_user)
    
    if current_user_id not in target_user.connections:
        target_user.connections.append(current_user_id)
        update_user(target_user)
    
    flash(f'You are now connected with {target_user.name}!', 'success')
    return redirect(url_for('profile.view_profile', user_id=user_id))

@profile_bp.route('/follow/<int:university_id>', methods=['POST'])
@student_required
def follow_university(university_id):
    student_id = session.get('user_id')
    student = get_user_by_id(student_id)
    university = get_user_by_id(university_id)
    
    if not university:
        flash('University not found', 'danger')
        return redirect(url_for('feed.home'))
    
    if university.user_type != 'university':
        flash('You can only follow universities', 'warning')
        return redirect(url_for('profile.view_profile', user_id=university_id))
    
    # Initialize followed_universities if it doesn't exist
    if not hasattr(student, 'followed_universities'):
        student.followed_universities = []
    
    # Add to followed universities
    if university_id not in student.followed_universities:
        student.followed_universities.append(university_id)
        update_user(student)
    
    # Add student to university's followers
    if student_id not in university.followers:
        university.followers.append(student_id)
        update_user(university)
    
    flash(f'You are now following {university.name}!', 'success')
    return redirect(url_for('profile.view_profile', user_id=university_id))

@profile_bp.route('/unfollow/<int:university_id>', methods=['POST'])
@student_required
def unfollow_university(university_id):
    student_id = session.get('user_id')
    student = get_user_by_id(student_id)
    university = get_user_by_id(university_id)
    
    if not university:
        flash('University not found', 'danger')
        return redirect(url_for('feed.home'))
    
    # Remove from followed universities
    if hasattr(student, 'followed_universities') and university_id in student.followed_universities:
        student.followed_universities.remove(university_id)
        update_user(student)
    
    # Remove student from university's followers
    if student_id in university.followers:
        university.followers.remove(student_id)
        update_user(university)
    
    flash(f'You have unfollowed {university.name}', 'info')
    return redirect(url_for('profile.view_profile', user_id=university_id))

@profile_bp.route('/disconnect/<int:user_id>', methods=['POST'])
@student_required
def disconnect_from_user(user_id):
    current_user_id = session.get('user_id')
    current_user = get_user_by_id(current_user_id)
    target_user = get_user_by_id(user_id)
    
    if not target_user:
        flash('User not found', 'danger')
        return redirect(url_for('feed.home'))
    
    # Remove from connections
    if user_id in current_user.connections:
        current_user.connections.remove(user_id)
        update_user(current_user)
    
    if current_user_id in target_user.connections:
        target_user.connections.remove(current_user_id)
        update_user(target_user)
    
    flash(f'You are no longer connected with {target_user.name}', 'info')
    return redirect(url_for('profile.view_profile', user_id=user_id))
