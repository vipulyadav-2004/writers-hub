import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()  # Initialize Migrate

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-key-123')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)  # Link Migrate to app and db
    
    login_manager.login_view = 'main.login_page'
    
    from project.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from project.routes import main
    app.register_blueprint(main)

    # Note: We usually stop using db.create_all() once using Migrations
    # but it doesn't hurt to keep it for the very first initialization.
    
    return app