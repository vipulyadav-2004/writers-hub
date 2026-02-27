import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()  # Initialize Migrate
oauth = OAuth()
csrf = CSRFProtect()

from werkzeug.middleware.proxy_fix import ProxyFix

def create_app():
    app = Flask(__name__)
    
    # Tell Flask it is behind a proxy (like Vercel) so it correctly resolves HTTPS URLs
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-key-123')
    # Default to SQLite if DATABASE_URL is not set (useful for local development)
    # Prefix 'postgresql://' instead of 'postgres://' if using SQLAlchemy >= 1.4
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)  # Link Migrate to app and db
    oauth.init_app(app)
    csrf.init_app(app)
    
    # Register Google OAuth
    oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    login_manager.login_view = 'main.login_page'
    
    from project.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from project.routes import main
    app.register_blueprint(main)

    # Note: We usually stop using db.create_all() once using Migrations
    # but it doesn't hurt to keep it for the very first initialization.
    with app.app_context():
        db.create_all()
    
    return app