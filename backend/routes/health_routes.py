"""Application health-check routes."""

from datetime import datetime, timezone
from services.email_service import EmailService
import socket
from flask import current_app

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
    

@health_bp.get("/smtp-test")
def smtp_test():
    server = current_app.config.get("MAIL_SERVER")
    port = current_app.config.get("MAIL_PORT")

    try:
        connection = socket.create_connection(
            (server, int(port)),
            timeout=10
        )

        remote = connection.getpeername()
        connection.close()

        return {
            "success": True,
            "message": "SMTP connection successful",
            "server": server,
            "port": port,
            "remote": str(remote)
        }

    except Exception as exc:
        return {
            "success": False,
            "message": "SMTP connection failed",
            "server": server,
            "port": port,
            "error_type": type(exc).__name__,
            "error": str(exc)
        }, 500