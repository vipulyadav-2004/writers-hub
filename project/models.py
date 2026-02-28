from datetime import datetime
from project import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Association table for followers
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# User model for the database
# UserMixin provides default implementations for Flask-Login requirements
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # Increased length for stronger hashes
    image_file = db.Column(db.String(500), nullable=False, default='default.jpg', server_default='default.jpg')
    is_verified = db.Column(db.Boolean, default=False)
    
    def get_verification_token(self, expires_sec=1800):
        from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
        from flask import current_app
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_token(token):
        from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
        from flask import current_app
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=1800)['user_id']
        except:
            return None
        return User.query.get(user_id)
    
    @property
    def is_developer(self):
        return self.email == 'vipulyadav0709@gmail.com'

    # Relationship: A user can have many posts
    # 'backref' adds a '.author' attribute to the Post model
    # 'lazy=True' means SQLAlchemy will load the data as needed
    posts = db.relationship('Post', backref='author', lazy=True)
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade="all, delete-orphan")
    saved_posts = db.relationship('SavedPost', backref='user', lazy='dynamic', cascade="all, delete-orphan")

    # Preferences settings
    msg_preference = db.Column(db.String(20), default='everyone') # everyone, followers, none
    profile_visibility = db.Column(db.String(20), default='public') # public, private
    two_factor_enabled = db.Column(db.Boolean, default=False)
    email_notif_enabled = db.Column(db.Boolean, default=True)
    feed_sorting = db.Column(db.String(20), default='latest') # latest, popular
    accent_color = db.Column(db.String(20), default='purple')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # Followers relationship
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
        
    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade="all, delete-orphan")

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_recent_notifications(self, limit=10):
        # We can safely order_by text inside the model file imported components
        return self.notifications.order_by(db.desc('timestamp')).limit(limit).all()

    def new_messages(self):
        return Message.query.filter_by(recipient=self, is_read=False).count()

    def get_top_chat_users(self, limit=10):
        messages = Message.query.filter(
            db.or_(Message.sender_id == self.id, Message.recipient_id == self.id)
        ).all()
        
        counts = {}
        for msg in messages:
            other_id = msg.recipient_id if msg.sender_id == self.id else msg.sender_id
            counts[other_id] = counts.get(other_id, 0) + 1
            
        sorted_user_ids = sorted(counts, key=counts.get, reverse=True)[:limit]
        
        # Fill remaining slots with followers
        if len(sorted_user_ids) < limit:
            followers = self.followers.all()
            for f in followers:
                if f.id not in sorted_user_ids and f.id != self.id:
                    sorted_user_ids.append(f.id)
                if len(sorted_user_ids) >= limit:
                    break
                    
        if not sorted_user_ids:
            return []
            
        users = User.query.filter(User.id.in_(sorted_user_ids)).all()
        users_dict = {user.id: user for user in users}
        return [users_dict[uid] for uid in sorted_user_ids if uid in users_dict]

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
    image_file = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    # Foreign key to link posts to users
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    likes = db.relationship('Like', backref='post', lazy='dynamic', cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade="all, delete-orphan")
    saved_by = db.relationship('SavedPost', backref='post', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Post {self.title}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_edited = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    image_file = db.Column(db.String(500), nullable=True)
    shared_post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)

    shared_post = db.relationship('Post', foreign_keys=[shared_post_id], backref='shared_in_messages')

    def __repr__(self):
        return f'<Message {self.id}>'

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<Like user:{self.user_id} post:{self.post_id}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    def __repr__(self):
        return f'<Comment {self.body[:20]}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True) # URL to redirect to when clicked
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification {self.message[:20]}>'

class SavedPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<SavedPost user:{self.user_id} post:{self.post_id}>'