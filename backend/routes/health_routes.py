"""Application health-check routes."""

from datetime import datetime, timezone
from services.email_service import EmailService

from flask import Blueprint, jsonify


health_bp = Blueprint(
    "health",
    __name__,
)


@health_bp.get("/health")
def health_check():
    """Return the current application health status."""

    return (
        jsonify(
            {
                "success": True,
                "status": "healthy",
                "service": "record-management-system",
                "timestamp": datetime.now(
                    timezone.utc,
                ).isoformat(),
            }
        ),
        200,
    )
    
