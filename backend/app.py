import os
from pathlib import Path
import inspect
import traceback
from datetime import datetime, timezone
from flask import Flask, app, jsonify, request, send_from_directory
from flask_cors import CORS
from flasgger import Swagger
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError as PydanticValidationError
from config import BASE_DIR, get_config
from extensions import db, jwt, migrate
from models import User
from auth.security import hash_password
from routes import (admin_bp,auth_bp,health_bp,records_bp,users_bp,)
from utils.exceptions import AppError, AuthenticationError
from utils.request_context import get_request_context
from utils.logging_config import configure_logging
import click

logger=configure_logging(BASE_DIR)
FRONTEND_DIR=BASE_DIR.parent/"frontend"

def safe_context(exc):
    """Capture precise exception location without leaking secrets."""
    tb=traceback.extract_tb(exc.__traceback__)
    last=tb[-1] if tb else None
    return {"exception":type(exc).__name__,"reason":str(exc),
            "file":last.filename if last else None,"function":last.name if last else None,"line":last.lineno if last else None}

def create_app():
    """Application factory: initialize extensions, folders, DB, seeds, routes and handlers."""
    # app=Flask(__name__,static_folder=None); app.config.from_object(Config)
    app=Flask(__name__,static_folder=None)
    config_class = get_config()
    app.config.from_object(config_class)
    logger.info("Starting application environment={} debug={}",os.getenv("FLASK_ENV", "development"),app.config["DEBUG"],)
    for folder in ("logs","uploads","static","templates"): (BASE_DIR/folder).mkdir(exist_ok=True)
    # db.init_app(app); jwt.init_app(app); CORS(app); Swagger(app,template={"info":{"title":"Record Management API","version":"1.0.0"}})
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(
        app,
        db,
        compare_type=True,
        render_as_batch=True,
    )
    CORS(app,origins=app.config["CORS_ORIGINS"],)
    Swagger(
    app,
    template={
        "info": {
            "title": "Record Management API",
            "version": "1.0.0",
            }
        },)
    for blueprint in (auth_bp,records_bp,users_bp,admin_bp,health_bp,):
        app.register_blueprint(blueprint)

    @app.before_request
    def request_log():
        logger.info("API Request method={} url={} ip={}",request.method,request.url,request.remote_addr)

    @app.after_request
    def response_log(response):
        logger.info("API Response method={} path={} status={}",request.method,request.path,response.status_code)
        return response

  
    @jwt.token_in_blocklist_loader
    def is_token_revoked(
        _jwt_header,
        jwt_payload,
    ):
        """Check whether the JWT session is inactive."""

        from models import TokenManager

        token_jti = jwt_payload["jti"]

        active_token = TokenManager.query.filter_by(
            jti=token_jti,
            is_active=True,
        ).first()

        return active_token is None

    @jwt.unauthorized_loader
    def missing(reason): return api_error(401,"Unauthorized","Authentication token is required",{"reason":reason})
    @jwt.invalid_token_loader
    def invalid(reason): return api_error(401,"Unauthorized","Invalid authentication token",{"reason":reason})
    @jwt.revoked_token_loader
    def revoked_response(_h,_p): return api_error(401,"Unauthorized","Authentication token is inactive")

    def api_error(code,error,message,details=None):
        return jsonify({"success":False,"status_code":code,"error":error,"message":message,
            "details":details or {},"timestamp":datetime.now(timezone.utc).isoformat()}),code

    # @app.errorhandler(AppError)
    # def app_error(exc):
    #     db.session.rollback()
    #     ctx=safe_context(exc)
    #     logger.bind(security=exc.status_code in (401,403)).opt(exception=True).error(
    #         "Exception={} Reason={} File={} Function={} Line={} Request={} {} IP={}",
    #         ctx["exception"],ctx["reason"],ctx["file"],ctx["function"],ctx["line"],request.method,request.path,request.remote_addr)
    #     details=exc.details if exc.status_code in (400,409,422) else {}
    #     return api_error(exc.status_code,exc.error,exc.message,details)
    @app.errorhandler(AppError)
    def app_error(exc):
        """Handle known application exceptions."""

        db.session.rollback()

        exception_context = safe_context(exc)

        request_context = get_request_context()

        logger.bind(
            security=exc.status_code in (
                401,
                403,
            )
        ).opt(
            exception=True,
        ).error(
            (
                "Application exception | "
                "exception={} | "
                "reason={} | "
                "file={} | "
                "function={} | "
                "line={} | "
                "method={} | "
                "url={} | "
                "user_id={} | "
                "user_email={} | "
                "role={} | "
                "ip={} | "
                "browser={} | "
                "os={} | "
                "device={}"
            ),
            exception_context["exception"],
            exception_context["reason"],
            exception_context["file"],
            exception_context["function"],
            exception_context["line"],
            request_context["http_method"],
            request_context["request_url"],
            request_context["user_id"],
            request_context["user_email"],
            request_context["user_role"],
            request_context["ip_address"],
            request_context["browser"],
            request_context["operating_system"],
            request_context["device_type"],
        )

        details = (
            exc.details
            if exc.status_code in (
                400,
                409,
                422,
            )
            else {}
        )

        return api_error(
            exc.status_code,
            exc.error,
            exc.message,
            details,
        )

    # @app.errorhandler(Exception)
    # def unexpected(exc):
    #     db.session.rollback()
    #     if isinstance(exc,HTTPException):
    #         return api_error(exc.code or 500,exc.name,exc.description)
    #     ctx=safe_context(exc)
    #     logger.opt(exception=True).error("Unexpected exception context={} request={} {} ip={} ua={}",
    #         ctx,request.method,request.url,request.remote_addr,request.headers.get("User-Agent"))
    #     safe={"exception":ctx["exception"],"reason":"Internal processing failure",
    #           "file":Path(ctx["file"]).name if ctx["file"] else None,"function":ctx["function"],"line":ctx["line"]}
    #     return api_error(500,"Internal Server Error","An unexpected error occurred.",safe)
    @app.errorhandler(Exception)
    def unexpected(exc):
        """Handle unexpected application exceptions."""

        db.session.rollback()

        if isinstance(
            exc,
            HTTPException,
        ):
            return api_error(
                exc.code or 500,
                exc.name,
                exc.description,
            )

        exception_context = safe_context(exc)

        request_context = get_request_context()

        logger.opt(
            exception=True,
        ).error(
            (
                "Unexpected exception | "
                "exception={} | "
                "reason={} | "
                "file={} | "
                "function={} | "
                "line={} | "
                "method={} | "
                "url={} | "
                "user_id={} | "
                "user_email={} | "
                "role={} | "
                "ip={} | "
                "browser={} | "
                "os={} | "
                "device={}"
            ),
            exception_context["exception"],
            exception_context["reason"],
            exception_context["file"],
            exception_context["function"],
            exception_context["line"],
            request_context["http_method"],
            request_context["request_url"],
            request_context["user_id"],
            request_context["user_email"],
            request_context["user_role"],
            request_context["ip_address"],
            request_context["browser"],
            request_context["operating_system"],
            request_context["device_type"],
        )

        if app.config["DEBUG"]:
            response_details = {
                "exception": exception_context["exception"],
                "reason": exception_context["reason"],
                "file": (
                    Path(
                        exception_context["file"]
                    ).name
                    if exception_context["file"]
                    else None
                ),
                "function": exception_context["function"],
                "line": exception_context["line"],
            }
        else:
            response_details = {}

        return api_error(
            500,
            "Internal Server Error",
            "An unexpected error occurred.",
            response_details,
        )

    @app.get("/")
    def root(): return send_from_directory(FRONTEND_DIR,"login.html")
    @app.get("/<path:filename>")
    def frontend(filename):
        target=FRONTEND_DIR/filename
        if target.is_file(): return send_from_directory(FRONTEND_DIR,filename)
        return send_from_directory(FRONTEND_DIR,"404.html"),404

    with app.app_context():
        if app.config["AUTO_CREATE_TABLES"]:
            logger.warning(
                "Automatic table creation is enabled. "
                "Use database migrations for production schema management."
            )

            db.create_all()

    @app.cli.command("seed-users")
    def seed_users_command() -> None:
        """Create the default seed users when they do not already exist."""

        try:
            seed_users()

            click.echo(
                "Seed user initialization completed successfully."
            )

        except Exception:
            db.session.rollback()

            logger.exception(
                "Seed user initialization failed."
            )

            raise click.ClickException(
                "Seed user initialization failed. "
                "Verify that database migrations are applied."
            )

    return app
def seed_users():
    """Idempotently seed sample admin and client accounts."""
    seeds=[("Client One","client1@gmail.com","CLIENT"),("Client Two","client2@gmail.com","CLIENT"),
           ("Client Three","client3@gmail.com","CLIENT"),("Admin One","admin1@gmail.com","ADMIN"),
           ("Admin Two","admin2@gmail.com","ADMIN")]
    changed=False
    for name,email,role in seeds:
        if not User.query.filter_by(email=email).first():
            db.session.add(User(full_name=name,email=email,password_hash=hash_password("Admin@123"),role=role)); changed=True
    if changed: db.session.commit(); logger.info("Seed users created")

# app=create_app()
# if __name__=="__main__":
#     app.run(host="127.0.0.1",port=5000,debug=True)
if __name__ == "__main__":
    application = create_app()

    application.run(
        host="127.0.0.1",
        port=5000,
        debug=application.config["DEBUG"],
    )