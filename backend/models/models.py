from datetime import datetime, timezone
import uuid as uuid_lib
from extensions import db

def utcnow():
    """Return timezone-aware UTC time."""
    return datetime.now(timezone.utc)

class User(db.Model):
    """Application user with ADMIN or CLIENT role."""
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    last_login = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class TokenManager(db.Model):
    """Persist login token metadata and active-token state."""
    __tablename__ = "token_manager"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    jti = db.Column(db.String(36),nullable=False,index=True,)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    login_ip = db.Column(db.String(64))
    browser = db.Column(db.String(120))
    operating_system = db.Column(db.String(120))
    device_type = db.Column(db.String(60))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    user = db.relationship("User", backref="tokens")

class MainTable(db.Model):
    """Main client record with workflow, locking, JSON snapshots and soft deletion."""
    __tablename__ = "main_table"
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.String(80), unique=True, nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    locked_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(30), default="PENDING", nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(20), nullable=False)
    fees = db.Column(db.Float, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    occupation = db.Column(db.String(120), nullable=False)
    blood_group = db.Column(db.String(10))
    nationality = db.Column(db.String(80), nullable=False)
    marital_status = db.Column(db.String(30))
    aadhaar = db.Column(db.String(12), nullable=False)
    pan = db.Column(db.String(10), nullable=False)
    remarks = db.Column(db.String(1000))
    input_json = db.Column(db.JSON, nullable=False)
    extracted_json = db.Column(db.JSON, nullable=False)
    validation_status = db.Column(db.String(30), default="VALID", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    approved_at = db.Column(db.DateTime(timezone=True))
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

class AuditLog(db.Model):
    """Immutable audit trail for data and workflow actions."""
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.String(80))
    old_data = db.Column(db.JSON)
    new_data = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
