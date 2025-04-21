from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import User
from sqlalchemy import or_, and_, func, cast, String
from app import db
import json

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
@login_required
def search():
    # Get search parameters
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
        
        # Get the initial results based on basic filters
        potential_results = search_query.all()
        results = []
        
        # Filter by skills for students
        if skills and (not user_type or user_type == 'student'):
            skill_list = [s.strip().lower() for s in skills.split(',')]
            
            for user in potential_results:
                if user.user_type == 'student':
                    # Use the property to get skills list
                    user_skills = []
                    try:
                        # Get skills safely using the property
                        if hasattr(user, 'skills_list') and user.skills_list:
                            user_skills = [s.lower() for s in user.skills_list]
                    except:
                        # Fallback if there's an error
                        pass
                        
                    # Check if any of the user's skills match the search skills
                    if any(skill in user_skills for skill in skill_list) or not user_skills:
                        results.append(user)
                else:
                    # Include non-students in results 
                    results.append(user)
        else:
            # If no skills filter or only looking for universities
            results = potential_results
        
        # Filter by programs (for universities)
        if programs and (not user_type or user_type == 'university'):
            programs_list = [p.strip().lower() for p in programs.split(',')]
            
            # Only apply this filter if we haven't already filtered by skills
            if not skills:
                results = potential_results
                
            filtered_results = []
            for user in results:
                if user.user_type == 'university':
                    # Check if programs match in description or other fields
                    description = (user.description or '').lower()
                    
                    # Include university if any program matches or description is empty
                    if any(program in description for program in programs_list) or not description:
                        filtered_results.append(user)
                else:
                    # Keep non-university users in the results
                    filtered_results.append(user)
            
            results = filtered_results
    
    # Add connection and following information
    if current_user.user_type == 'student':
        # In a real implementation, we'd fetch the connections from join tables
        # For now, we'll make sure each result has the needed properties
        for result in results:
            if result.user_type == 'student':
                # Check if student is connected
                result.is_connected = False  # Placeholder
                # In a proper implementation: 
                # result.is_connected = StudentConnection.query.filter(
                #     and_(
                #         StudentConnection.student1_id == current_user.id,
                #         StudentConnection.student2_id == result.id
                #     )
                # ).first() is not None
            elif result.user_type == 'university':
                # Check if student is following university
                result.is_following = False  # Placeholder
                # In a proper implementation:
                # result.is_following = UniversityFollower.query.filter(
                #     and_(
                #         UniversityFollower.student_id == current_user.id,
                #         UniversityFollower.university_id == result.id
                #     )
                # ).first() is not None
    
    return render_template(
        'search.html', 
        query=query, 
        results=results,
        user_type=user_type,
        location=location,
        skills=skills,
        programs=programs
    )

# API endpoint for search suggestions
@search_bp.route('/api/search/suggestions')
@login_required
def search_suggestions():
    query = request.args.get('q', '')
    user_type = request.args.get('type', '')
    
    if not query or len(query) < 2:
        return jsonify([])
    
    # Build search query
    search_query = User.query
    
    # Filter by user type if specified
    if user_type in ['student', 'university']:
        search_query = search_query.filter(User.user_type == user_type)
    
    # Search by name
    search_query = search_query.filter(User.name.ilike(f'%{query}%'))
    
    # Limit to 10 results
    suggestions = search_query.limit(10).all()
    
    # Format results
    results = []
    for user in suggestions:
        result = {
            'id': user.id,
            'name': user.name,
            'type': user.user_type,
        }
        
        # Add type-specific details
        if user.user_type == 'student':
            result['subtitle'] = user.bio[:50] + '...' if user.bio and len(user.bio) > 50 else 'Student'
        else:
            result['subtitle'] = user.location or 'University'
            
        results.append(result)
    
    return jsonify(results)
