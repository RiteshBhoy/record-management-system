from flask import Blueprint, request
from pydantic import ValidationError as PydanticValidationError
from extensions import db
from models import User
from schemas import UserCreateSchema, UserUpdateSchema
from auth.security import hash_password
from middleware.auth import current_user, roles_required
from services.audit_service import audit
from utils.exceptions import ValidationError, DuplicateRecordError, ResourceNotFoundError
from utils.helpers import success, pydantic_errors, iso

users_bp=Blueprint("users",__name__,url_prefix="/api/users")
def ud(u): return {"id":u.id,"uuid":u.uuid,"full_name":u.full_name,"email":u.email,"role":u.role,"status":u.status,"last_login":iso(u.last_login)}

@users_bp.get("")
@roles_required("ADMIN")
def users():
    """List users."""
    return success("Users fetched",[ud(x) for x in User.query.order_by(User.id).all()])

@users_bp.post("")
@roles_required("ADMIN")
def create():
    """Create a user."""
    actor=current_user()
    try: p=UserCreateSchema.model_validate(request.get_json(silent=True) or {})
    except PydanticValidationError as exc: raise ValidationError("Validation Failed",pydantic_errors(exc))
    if User.query.filter_by(email=str(p.email).lower()).first(): raise DuplicateRecordError("Duplicate email")
    u=User(full_name=p.full_name,email=str(p.email).lower(),password_hash=hash_password(p.password),role=p.role)
    db.session.add(u); audit(actor.id,"CREATE_USER","users",new_data={"email":u.email,"role":u.role}); db.session.commit()
    return success("User created",ud(u),201)

@users_bp.put("/<int:user_id>")
@roles_required("ADMIN")
def update(user_id):
    """Update safe user profile fields."""
    actor=current_user(); u=db.session.get(User,user_id)
    if not u: raise ResourceNotFoundError("User not found")
    try: p=UserUpdateSchema.model_validate(request.get_json(silent=True) or {})
    except PydanticValidationError as exc: raise ValidationError("Validation Failed",pydantic_errors(exc))
    old=ud(u)
    for k,v in p.model_dump(exclude_none=True).items():
        if k=="role": v=v.upper()
        setattr(u,k,v)
    audit(actor.id,"UPDATE_USER","users",str(u.id),old,ud(u)); db.session.commit()
    return success("User updated",ud(u))

@users_bp.delete("/<int:user_id>")
@roles_required("ADMIN")
def delete(user_id):
    """Deactivate a user instead of physically deleting it."""
    actor=current_user(); u=db.session.get(User,user_id)
    if not u: raise ResourceNotFoundError("User not found")
    u.status="INACTIVE"; audit(actor.id,"DEACTIVATE_USER","users",str(u.id),new_data={"status":"INACTIVE"}); db.session.commit()
    return success("User deactivated")
