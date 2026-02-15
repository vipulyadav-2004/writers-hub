from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort
from flask_login import login_user, logout_user, current_user, login_required
from project.models import User, Post
from project.forms import LoginForm, RegistrationForm, PostForm
from project import db, oauth
from flask_wtf.csrf import CSRFError

main = Blueprint('main', __name__)

@main.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('Security token missing or invalid. Please try again.', 'danger')
    return redirect(request.referrer or url_for('main.main_page'))

@main.route('/')
def main_page():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)

@main.route("/register", methods=['GET', 'POST'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('main.main_page'))
    
    form = RegistrationForm() # Step 1: Initialize the form
    
    if form.validate_on_submit(): # Step 2: Use validate_on_submit
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('main.login_page'))
    
    # Step 3: Pass form=form to the template
    return render_template('register.html', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('main.main_page'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('main.profile_page'))
        else:
            flash('Login failed. Please check email and password.', 'danger')
            
    return render_template('login.html', form=form)

@main.route('/login/google')
def google_login():
    redirect_uri = url_for('main.google_authorize', _external=True)
    print(f"DEBUG: Redirect URI being sent: {redirect_uri}")
    return oauth.google.authorize_redirect(redirect_uri)

@main.route('/login/google/callback')
def google_authorize():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    if not user_info:
        # Fallback if userinfo not in token (depends on scope/provider)
        user_info = oauth.google.userinfo()
    
    if not user_info:
        flash('Failed to fetch user info from Google.', 'danger')
        return redirect(url_for('main.login_page'))
        
    email = user_info.get('email')
    if not email:
        flash('Google account does not have a verified email.', 'danger')
        return redirect(url_for('main.login_page'))

    # Check if user exists
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Create new user
        # Generate a unique username based on email or name
        base_username = user_info.get('name', '').replace(' ', '').lower() or email.split('@')[0]
        # Ensure username is unique
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
            
        user = User(
            username=username,
            email=email,
            # password_hash is optional/nullable, so we can leave it empty
            # or set a random unguessable password if desired
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created via Google!', 'success')
    else:
        flash('Logged in via Google!', 'success')

    login_user(user)
    return redirect(url_for('main.main_page'))

@main.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data, 
            body=form.body.data, 
            author_name=form.author_name.data,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        return redirect(url_for('main.main_page'))
    
    return render_template('create_post.html', form=form, legend='Create New Post', title='New Post')

@main.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        post.author_name = form.author_name.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('main.main_page'))
    elif request.method == 'GET':
        form.title.data = post.title
        form.body.data = post.body
        form.author_name.data = post.author_name
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

@main.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    print(f"DEBUG: Attempting to delete post {post_id}")
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        print(f"DEBUG: Permission denied for user {current_user}")
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    print(f"DEBUG: Post {post_id} deleted successfully")
    
    # Redirect to the page the user came from, or main page if unknown
    # If the user deleted the post from a single post view (which no longer exists), fallback to main page.
    # We check if 'profile' is in the referrer to return them to the profile page.
    next_page = request.referrer
    if next_page and 'profile' in next_page:
        return redirect(url_for('main.profile_page'))
    
    # Otherwise, default to the main page feed
    return redirect(url_for('main.main_page'))

@main.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('main.main_page'))

@main.route('/profile')
@login_required
def profile_page():
    # Fetch only posts belonging to the logged-in user
    user_posts = Post.query.filter_by(author=current_user).order_by(Post.timestamp.desc()).all()
    return render_template('profile.html', username=current_user.username, posts=user_posts)


@main.route('/search')
def search():
    query = request.args.get('q')
    if query:
        # Search users by username (case insensitive)
        users = User.query.filter(User.username.ilike(f'%{query}%')).all()
    else:
        users = []
    
    return render_template('search_results.html', users=users, query=query)

@main.route('/user/<username>')
def user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts, title=f"Posts by {user.username}")