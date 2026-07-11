"""Utilities for safely collecting request and user context."""

from typing import Any, Dict

from flask import request
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    verify_jwt_in_request,
)
from user_agents import parse

from extensions import db
from models import User


def get_request_context() -> Dict[str, Any]:
    """Collect safe debugging context for the current HTTP request.

    The function never raises an exception intentionally. Error logging
    must not cause another application error while handling the original
    exception.
    """

    context: Dict[str, Any] = {
        "request_url": request.url,
        "request_path": request.path,
        "http_method": request.method,
        "ip_address": _get_client_ip(),
        "browser": None,
        "operating_system": None,
        "device_type": None,
        "user_id": None,
        "user_email": None,
        "user_role": None,
    }

    try:
        user_agent = parse(
            request.headers.get(
                "User-Agent",
                "",
            )
        )

        context["browser"] = (
            f"{user_agent.browser.family} "
            f"{user_agent.browser.version_string}"
        ).strip()

        context["operating_system"] = (
            f"{user_agent.os.family} "
            f"{user_agent.os.version_string}"
        ).strip()

        if user_agent.is_mobile:
            context["device_type"] = "Mobile"
        elif user_agent.is_tablet:
            context["device_type"] = "Tablet"
        elif user_agent.is_pc:
            context["device_type"] = "PC"
        else:
            context["device_type"] = "Other"

    except Exception:
        context["browser"] = "Unknown"
        context["operating_system"] = "Unknown"
        context["device_type"] = "Unknown"

    try:
        verify_jwt_in_request(
            optional=True,
        )

        user_identity = get_jwt_identity()

        if user_identity:
            user = db.session.get(
                User,
                int(user_identity),
            )

            if user:
                context["user_id"] = user.id
                context["user_email"] = user.email
                context["user_role"] = user.role

    except Exception:
        # Never allow context collection to hide the original exception.
        pass

    return context


def _get_client_ip() -> str:
    """Return the best available client IP address."""

    forwarded_for = request.headers.get(
        "X-Forwarded-For",
        "",
    )

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.remote_addr or "Unknown"