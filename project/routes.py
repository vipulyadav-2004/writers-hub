from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from google.oauth2 import id_token
from google.auth.transport import requests
from project.models import User, Post
from project import db

main = Blueprint('main', __name__)

GOOGLE_CLIENT_ID = "572405532813-apsop71t59dsalip1lra5dldafv8b70l.apps.googleusercontent.com"
@main.route('/')
def main_page():
    # Fetch all posts for the feed
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)

@main.route("/register", methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user exists
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered.', 'danger')
            return redirect(url_for('main.register_page'))
            
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('main.login_page'))
    return render_template('register.html')

@main.route("/login", methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.profile_page'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
            
    return render_template('login.html')

@main.route('/api/auth/google', methods=['POST'])
def google_auth():
    token = request.json.get('token')
    
    try:
        # Verify the token with Google
        # This checks the signature, the expiration, and the intended audience (your app)
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

        # ID info contains user data
        userid = idinfo['sub']  # Unique Google ID
        email = idinfo['email']
        name = idinfo.get('name')
        picture = idinfo.get('picture')

        # Logic for your database:
        # user = User.query.filter_by(google_id=userid).first()
        # if not user:
        #     create_new_user(userid, email, name)

        # Start a Flask session
        session['user_id'] = userid
        session['logged_in'] = True

        return jsonify({"status": "success", "user": name}), 200

    except ValueError:
        # Invalid token
        return jsonify({"status": "error", "message": "Invalid token"}), 400

@main.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('main.main_page'))

@main.route('/profile')
@login_required
def profile_page():
    # current_user is provided by Flask-Login
    return render_template('profile.html', username=current_user.username)

@main.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        author_name = request.form.get('author_name')
        body = request.form.get('body')
        
        post = Post(title=title, author_name=author_name, body=body, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        return redirect(url_for('main.main_page'))
    return render_template('create_post.html')