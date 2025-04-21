from flask import Blueprint, render_template, request, session
from data_store import search_users, get_user_by_id
from auth import login_required

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    user_type = request.args.get('type', '')
    
    results = []
    
    if query:
        if user_type in ['student', 'university']:
            results = search_users(query, user_type)
        else:
            results = search_users(query)
    
    current_user_id = session.get('user_id')
    current_user = get_user_by_id(current_user_id)
    
    # For students, check if already connected or following
    if current_user and current_user.user_type == 'student':
        for result in results:
            if result.user_type == 'student':
                result.is_connected = result.id in current_user.connections
            elif result.user_type == 'university':
                followed_universities = getattr(current_user, 'followed_universities', [])
                result.is_following = result.id in followed_universities
    
    return render_template(
        'search.html', 
        query=query, 
        results=results,
        user_type=user_type
    )
