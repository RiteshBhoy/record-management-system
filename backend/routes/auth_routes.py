from datetime import datetime, timezone
from flask import Blueprint, request
from flask_jwt_extended import (create_access_token,decode_token,get_jwt,get_jwt_identity,jwt_required,)
from pydantic import ValidationError as PydanticValidationError
from user_agents import parse
from extensions import db
from models import User, TokenManager
from schemas import LoginSchema
from auth.security import verify_password
from middleware.auth import current_user
from utils.exceptions import AuthenticationError, ValidationError
from utils.helpers import success, pydantic_errors, iso
from loguru import logger

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.post("/login")
def login():
    """Authenticate, invalidate old tokens and persist login metadata."""
    try: payload = LoginSchema.model_validate(request.get_json(silent=True) or {})
    except PydanticValidationError as exc: raise ValidationError("Validation Failed", pydantic_errors(exc))
    user = User.query.filter_by(email=str(payload.email).lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        logger.bind(security=True).warning("Authentication failure for email={}", payload.email)
        raise AuthenticationError("Invalid email or password")
    if user.status != "ACTIVE": raise AuthenticationError("User account is inactive")
    TokenManager.query.filter_by(user_id=user.id, is_active=True).update({"is_active": False})
    # token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "email": user.email})
    token = create_access_token(
    identity=str(user.id),
    additional_claims={
        "role": user.role,
        "email": user.email,
    },)
    decoded_token = decode_token(token)
    token_jti = decoded_token["jti"]
    ua = parse(request.headers.get("User-Agent", ""))
    
    tm = TokenManager(
        user_id=user.id,
        jti=token_jti,
        expires_at=datetime.fromtimestamp(
            decoded_token["exp"],
            timezone.utc,
        ),
        login_ip=request.headers.get(
            "X-Forwarded-For",
            request.remote_addr,
        ),
        browser=(
            f"{ua.browser.family} "
            f"{ua.browser.version_string}"
        ),
        operating_system=(
            f"{ua.os.family} "
            f"{ua.os.version_string}"
        ),
        device_type=(
            "Mobile"
            if ua.is_mobile
            else "Tablet"
            if ua.is_tablet
            else "PC"
        ),
    )
    user.last_login = datetime.now(timezone.utc)
    db.session.add(tm); db.session.commit()
    return success("Login successful", {"access_token": token, "role": user.role,
        "user": {"id": user.id, "uuid": user.uuid, "full_name": user.full_name, "email": user.email, "role": user.role}})


@auth_bp.post("/logout")
@jwt_required()
def logout():
    """Invalidate the current JWT session using its JTI."""

    jwt_payload = get_jwt()

    token_jti = jwt_payload["jti"]

    TokenManager.query.filter_by(
        jti=token_jti,
        is_active=True,
    ).update(
        {
            "is_active": False,
        }
    )

    db.session.commit()

    logger.bind(
        security=True,
    ).info(
        "User logout completed user_id={}",
        get_jwt_identity(),
    )

    return success(
        "Logout successful"
    )

@auth_bp.get("/profile")
def profile():
    """Return authenticated user's profile."""
    u = current_user()
    return success("Profile fetched", {"id":u.id,"uuid":u.uuid,"full_name":u.full_name,
        "email":u.email,"role":u.role,"status":u.status,"last_login":iso(u.last_login)})


@auth_bp.get("/validate-token")
def validate_token():
    """Validate the JWT and its active server-side session."""

    user = current_user()

    jwt_payload = get_jwt()

    token_jti = jwt_payload["jti"]

    active_token = TokenManager.query.filter_by(
        user_id=user.id,
        jti=token_jti,
        is_active=True,
    ).first()

    if not active_token:
        raise AuthenticationError(
            "Token is inactive"
        )

    return success(
        "Token is valid",
        {
            "role": user.role,
        },
    )
