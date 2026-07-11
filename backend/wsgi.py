"""WSGI entry point for production application servers.

Production WSGI servers such as Gunicorn import the Flask application
object from this module.
"""

from app import create_app


app = create_app()