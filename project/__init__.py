import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize the database extension
db = SQLAlchemy()

def create_app():
    """
    Application factory to create and configure the Flask app.
    """
    app = Flask(__name__)

    # --- SECURE SECRET KEY ---
    # We look for 'FLASK_SECRET_KEY' in the environment (e.g., from a .env file).
    # If not found, it defaults to a development-only key.
    # Make sure to install python-dotenv: pip install python-dotenv
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-key-for-local-testing-only')
    
    # Database Configuration
    # This creates a 'site.db' file in your project root.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the app instance
    db.init_app(app)

    # Register the Blueprint (contains your main_page, login_page, and profile_page)
    from project.routes import main
    app.register_blueprint(main)

    # Automatically create the database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app