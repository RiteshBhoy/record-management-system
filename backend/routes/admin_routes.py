from flask import Blueprint, request
from sqlalchemy import func
from extensions import db
from models import AuditLog, TokenManager, MainTable, User
from middleware.auth import roles_required
from utils.helpers import success, iso

admin_bp=Blueprint("admin",__name__,url_prefix="/api/admin")

@admin_bp.get("/stats")
@roles_required("ADMIN")
def stats():
    """Return dashboard statistics."""
    return success("Statistics fetched",{
        "records":MainTable.query.filter_by(is_deleted=False).count(),
        "pending":MainTable.query.filter_by(is_deleted=False,status="PENDING").count(),
        "approved":MainTable.query.filter_by(is_deleted=False,status="APPROVED").count(),
        "clients":User.query.filter_by(role="CLIENT",status="ACTIVE").count()})

@admin_bp.get("/audit-logs")
@roles_required("ADMIN")
def audits():
    """Return latest audit events."""
    rows=AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(500).all()
    return success("Audit logs fetched",[{"id":x.id,"user_id":x.user_id,"action":x.action,"table_name":x.table_name,
        "record_id":x.record_id,"old_data":x.old_data,"new_data":x.new_data,"timestamp":iso(x.timestamp)} for x in rows])

@admin_bp.get("/login-history")
@roles_required("ADMIN")
def history():
    """Return latest login history."""
    rows=TokenManager.query.order_by(TokenManager.created_at.desc()).limit(500).all()
    return success("Login history fetched",[{"id":x.id,"user_id":x.user_id,"email":x.user.email,
        "is_active":x.is_active,"login_ip":x.login_ip,"browser":x.browser,"operating_system":x.operating_system,
        "device_type":x.device_type,"created_at":iso(x.created_at)} for x in rows])
