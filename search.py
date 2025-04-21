from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import User
from sqlalchemy import or_
import json

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    user_type = request.args.get('type', '')
    location = request.args.get('location', '')
    skills = request.args.get('skills', '')
    programs = request.args.get('programs', '')
    
    results = []
    
    if query or location or skills or programs:
        # Start with base query
        search_query = User.query
        
        # Filter by user type if specified
        if user_type in ['student', 'university']:
            search_query = search_query.filter(User.user_type == user_type)
        
        # Filter by name or email if query is provided
        if query:
            search_query = search_query.filter(
                or_(
                    User.name.ilike(f'%{query}%'),
                    User.email.ilike(f'%{query}%')
                )
            )
        
        # Filter by location if provided
        if location:
            search_query = search_query.filter(User.location.ilike(f'%{location}%'))
        
        # Filter by skills for students
        if skills and (not user_type or user_type == 'student'):
            # This is more complex since skills are stored as JSON
            # For a proper solution, we'd need a different database schema or full-text search
            # For now, we'll filter in Python after the query
            potential_results = search_query.all()
            results = []
            
            skill_list = [s.strip().lower() for s in skills.split(',')]
            for user in potential_results:
                if user.user_type == 'student':
                    user_skills = [s.lower() for s in user.skills_list]
                    if any(skill in user_skills for skill in skill_list):
                        results.append(user)
                else:
                    results.append(user)
        else:
            # If no skills filter or only looking for universities
            results = search_query.all()
        
        # For programs filter (universities), we'd do something similar to skills
        if programs and (not user_type or user_type == 'university'):
            # Similarly, for a proper solution, we'd need a different db schema
            # This is a simplified version
            if not skills:  # If we haven't already filtered
                results = search_query.all()
                
            filtered_results = []
            for user in results:
                if user.user_type == 'university':
                    if programs.lower() in user.description.lower():
                        filtered_results.append(user)
                else:
                    filtered_results.append(user)
            
            results = filtered_results
    
    # For students, check if already connected or following
    if current_user.user_type == 'student':
        # In a real implementation, we'd fetch the connections from the join table
        # Here, we're setting dummy values for now
        for result in results:
            if result.user_type == 'student':
                # Check student connections
                result.is_connected = False  # Placeholder
            elif result.user_type == 'university':
                # Check university following
                result.is_following = False  # Placeholder
    
    return render_template(
        'search.html', 
        query=query, 
        results=results,
        user_type=user_type,
        location=location,
        skills=skills,
        programs=programs
    )
