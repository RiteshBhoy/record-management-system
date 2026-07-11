from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from extensions import db
from models import User
from utils.exceptions import AuthenticationError, AuthorizationError

def current_user():
    """Resolve the authenticated user from JWT identity."""
    verify_jwt_in_request()
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or user.status != "ACTIVE":
        raise AuthenticationError("User account is unavailable")
    return user

def roles_required(*roles):
    """Restrict a route to one or more roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user.role not in roles:
                raise AuthorizationError("You do not have permission to perform this action")
            return fn(*args, **kwargs)
        return wrapper
    return decorator
