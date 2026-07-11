"""Flask extension instances.

Extensions are created without a Flask application here. They are attached
to the application inside the application factory.
"""

from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

jwt = JWTManager()

migrate = Migrate()