from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initializing the database
db = SQLAlchemy()


def create_app(config_name=None):
    """
    Creating the Flask app factory function.
    """
    app = Flask(__name__)
    
    # Configure database based on environment
    if config_name == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        # We fetch the database URL from environment variable
        database_connection_string = os.getenv('DATABASE_URL')
        app.config['SQLALCHEMY_DATABASE_URI'] = database_connection_string
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Start SQLAlchemy with the app
    db.init_app(app)
    
    # Create database tables within app context
    with app.app_context():
        from app.models import Task, Category
        db.create_all()
    
    # Register routes
    from app.routes import tasks, categories
    tasks.register_routes(app)
    categories.register_routes(app)
    
    return app
