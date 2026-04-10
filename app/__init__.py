from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initializing the database
db = SQLAlchemy()


def create_app():
    """
    Creating the Flask app factory function.
    """
    app = Flask(__name__)
    
    # We fetch the database URL from environment variable
    database_connection_string = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_connection_string
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Start SQLAlchemy with the app
    db.init_app(app)
    
    # This part will be coded later after the routes are defined
    # from app.routes import tasks_bp, categories_bp
    # app.register_blueprint(tasks_bp)
    # app.register_blueprint(categories_bp)
    
    # Create database tables within app context
    with app.app_context():
        db.create_all()
    
    return app
