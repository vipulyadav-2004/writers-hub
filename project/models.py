from datetime import datetime
from project import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# User model for the database
# UserMixin provides default implementations for Flask-Login requirements
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # Increased length for stronger hashes
    
    # Relationship: A user can have many posts
    # 'backref' adds a '.author' attribute to the Post model
    # 'lazy=True' means SQLAlchemy will load the data as needed
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

# Post model for the database
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    # Foreign key to link posts to users
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Post {self.title}>'