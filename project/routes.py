from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort, current_app
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy import or_, and_
from project.models import User, Post, Message, Like, Comment, Notification
from project.forms import LoginForm, RegistrationForm, PostForm, UpdateProfileForm, MessageForm, UpdatePasswordForm, UpdateEmailForm, DeleteAccountForm, PreferencesForm
from project import db, oauth
from flask_wtf.csrf import CSRFError
import secrets
import os
from PIL import Image

main = Blueprint('main', __name__)

@main.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('Security token missing or invalid. Please try again.', 'danger')
    return redirect(request.referrer or url_for('main.main_page'))

import cloudinary
import cloudinary.uploader

def save_picture(form_picture, folder):
    # Depending on your form inputs, you may want to optimize the original before sending
    # or you can rely on Cloudinary's native optimization API! Let's resize in pillow 
    # and send the raw bytes up to save bandwidth
    output_size = (1200, 1200)
    if folder == 'profile_pics':
        output_size = (250, 250)
    
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    
    import io
    # Convert PIL Image back to byte stream so Cloudinary can receive it
    byte_io = io.BytesIO()
    # Handle PNG vs JPEG format preservation
    img_format = i.format if i.format else 'JPEG'
    i.save(byte_io, format=img_format)
    byte_io.seek(0)
    
    # Upload byte stream directly to cloudinary folder
    # Assigns it a dynamic unique ID
    response = cloudinary.uploader.upload(
        byte_io, 
        folder=f"writers_hub/{folder}", 
        resource_type="image"
    )
    
    # Cloudinary return a JSON blob, we just want the direct image URL string to save to our Database
    return response.get("secure_url")

@main.route('/')
def main_page():
    if current_user.is_authenticated:
        posts_query = current_user.followed_posts()
        if current_user.feed_sorting == 'popular':
            from sqlalchemy import func
            posts = posts_query.outerjoin(Like).group_by(Post.id).order_by(func.count(Like.id).desc(), Post.timestamp.desc()).all()
        else:
            posts = posts_query.all()
    else:
        posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)

@main.route('/explore')
def explore_page():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    if current_user.is_authenticated and current_user.feed_sorting == 'popular':
        from sqlalchemy import func
        posts = Post.query.outerjoin(Like).group_by(Post.id).order_by(func.count(Like.id).desc(), Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts, title="Explore Feed")

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
        picture_file = None
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 'post_pics')
            
        post = Post(
            title=form.title.data, 
            body=form.body.data, 
            author_name=form.author_name.data,
            image_file=picture_file,
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
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 'post_pics')
            post.image_file = picture_file
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

@main.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if like:
        db.session.delete(like)
        db.session.commit()
    else:
        new_like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(new_like)
        if post.author != current_user:
            notif = Notification(user_id=post.author.id, message=f"{current_user.username} liked your post '{post.title[:20]}...'", link=url_for('main.user_posts', username=current_user.username))
            db.session.add(notif)
        db.session.commit()
        
    return redirect(request.referrer or url_for('main.main_page'))

@main.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    body = request.form.get('body')
    
    if body and body.strip():
        comment = Comment(body=body.strip(), user_id=current_user.id, post_id=post_id)
        db.session.add(comment)
        if post.author != current_user:
            notif = Notification(user_id=post.author.id, message=f"{current_user.username} commented on your post '{post.title[:20]}...'", link=url_for('main.user_posts', username=current_user.username))
            db.session.add(notif)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    else:
        flash('Comment cannot be empty.', 'danger')
        
    return redirect(request.referrer or url_for('main.main_page'))

@main.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('main.main_page'))

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 'profile_pics')
            current_user.image_file = picture_file
        if form.username.data != current_user.username:
            current_user.username = form.username.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.profile_page'))
    elif request.method == 'GET':
        form.username.data = current_user.username

    # Fetch only posts belonging to the logged-in user
    user_posts = Post.query.filter_by(author=current_user).order_by(Post.timestamp.desc()).all()
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file) if current_user.image_file else url_for('static', filename='profile_pics/default.jpg')
    return render_template('profile.html', username=current_user.username, posts=user_posts, form=form, image_file=image_file)

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    password_form = UpdatePasswordForm()
    email_form = UpdateEmailForm()
    delete_form = DeleteAccountForm()
    prefs_form = PreferencesForm()
    
    # Pre-populate forms
    if request.method == 'GET':
        email_form.email.data = current_user.email
        prefs_form.msg_preference.data = current_user.msg_preference
        prefs_form.profile_visibility.data = current_user.profile_visibility
        prefs_form.two_factor_enabled.data = current_user.two_factor_enabled
        prefs_form.email_notif_enabled.data = current_user.email_notif_enabled
        prefs_form.feed_sorting.data = current_user.feed_sorting
        prefs_form.accent_color.data = current_user.accent_color

    # Determine which form was submitted via a hidden field or distinct submit buttons
    if 'submit_prefs' in request.form and prefs_form.validate_on_submit():
        current_user.msg_preference = prefs_form.msg_preference.data
        current_user.profile_visibility = prefs_form.profile_visibility.data
        current_user.two_factor_enabled = prefs_form.two_factor_enabled.data
        current_user.email_notif_enabled = prefs_form.email_notif_enabled.data
        current_user.feed_sorting = prefs_form.feed_sorting.data
        current_user.accent_color = prefs_form.accent_color.data
        db.session.commit()
        flash('Preferences updated successfully!', 'success')
        return redirect(url_for('main.settings_page'))
    if 'submit_password' in request.form and password_form.validate_on_submit():
        if current_user.password_hash and current_user.check_password(password_form.current_password.data):
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('main.settings_page'))
        else:
            flash('Current password is incorrect.', 'danger')

    if 'submit_email' in request.form and email_form.validate_on_submit():
        current_user.email = email_form.email.data
        db.session.commit()
        flash('Your email address has been updated!', 'success')
        return redirect(url_for('main.settings_page'))
        
    if 'submit_delete' in request.form and delete_form.validate_on_submit():
        user = User.query.get(current_user.id)
        logout_user()
        db.session.delete(user)
        db.session.commit()
        flash('Your account has been permanently deleted.', 'info')
        return redirect(url_for('main.main_page'))

    return render_template('settings.html', 
                           password_form=password_form, 
                           email_form=email_form, 
                           delete_form=delete_form,
                           prefs_form=prefs_form)

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
    return render_template('index.html', posts=posts, user=user, title=f"Posts by {user.username}")

@main.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'User {username} not found.', 'danger')
        return redirect(url_for('main.main_page'))
    if user == current_user:
        flash('You cannot follow yourself!', 'warning')
        return redirect(url_for('main.user_posts', username=username))
    current_user.follow(user)
    notif = Notification(user_id=user.id, message=f"{current_user.username} started following you", link=url_for('main.user_posts', username=current_user.username))
    db.session.add(notif)
    db.session.commit()
    flash(f'You are following {username}!', 'success')
    return redirect(request.referrer or url_for('main.user_posts', username=username))

@main.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'User {username} not found.', 'danger')
        return redirect(url_for('main.main_page'))
    if user == current_user:
        flash('You cannot unfollow yourself!', 'warning')
        return redirect(url_for('main.user_posts', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You are not following {username}.', 'info')
    return redirect(request.referrer or url_for('main.user_posts', username=username))

@main.route('/user/<username>/followers')
@login_required
def followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    users = user.followers.all()
    return render_template('users_list.html', users=users, user=user, title="Followers")

@main.route('/user/<username>/following')
@login_required
def following(username):
    user = User.query.filter_by(username=username).first_or_404()
    users = user.followed.all()
    return render_template('users_list.html', users=users, user=user, title="Following")

@main.route("/messages")
@login_required
def messages():
    messages_query = Message.query.filter(
        or_(Message.sender_id == current_user.id,
            Message.recipient_id == current_user.id)
    ).order_by(Message.timestamp.desc()).all()
    
    chat_users = []
    seen_ids = set()
    
    for msg in messages_query:
        other_user_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
        if other_user_id not in seen_ids:
            seen_ids.add(other_user_id)
            other_user = User.query.get(other_user_id)
            if other_user:
                chat_users.append({'user': other_user, 'last_message': msg})
                
    return render_template('messages.html', chat_users=chat_users, title="Messages")

@main.route("/chat/<username>", methods=['GET', 'POST'])
@login_required
def chat(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        flash('You cannot chat with yourself.', 'warning')
        return redirect(url_for('main.messages'))
        
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, body=form.message.data)
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 'message_pics')
            msg.image_file = picture_file
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for('main.chat', username=username))
        
    chat_messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == user.id),
            and_(Message.sender_id == user.id, Message.recipient_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    # Mark messages as read
    unread_messages = Message.query.filter_by(sender_id=user.id, recipient_id=current_user.id, is_read=False).all()
    if unread_messages:
        for m in unread_messages:
            m.is_read = True
        db.session.commit()
    
    return render_template('chat.html', user=user, chat_messages=chat_messages, form=form, title=f"Chat with {user.username}")

@main.route("/message/<int:message_id>/edit", methods=['POST'])
@login_required
def edit_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.author != current_user:
        abort(403)
    
    new_body = request.form.get('body')
    if new_body and new_body.strip():
        message.body = new_body.strip()
        message.is_edited = True
        db.session.commit()
        flash('Message updated successfully.', 'success')
    else:
        flash('Message cannot be empty.', 'danger')
        
    return redirect(request.referrer or url_for('main.messages'))

@main.route("/message/<int:message_id>/delete", methods=['POST'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.author != current_user:
        abort(403)
        
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(request.referrer or url_for('main.messages'))

@main.route("/share_post/<int:post_id>", methods=['POST'])
@login_required
def share_post(post_id):
    post = Post.query.get_or_404(post_id)
    recipient_username = request.form.get('recipient')
    message_text = request.form.get('message_text', '')
    
    recipient = User.query.filter_by(username=recipient_username).first()
    if not recipient:
        flash('User not found to share with.', 'danger')
        return redirect(request.referrer or url_for('main.main_page'))
        
    if recipient == current_user:
        flash('You cannot share a post with yourself.', 'warning')
        return redirect(request.referrer or url_for('main.main_page'))

    msg = Message(
        author=current_user,
        recipient=recipient,
        body=message_text,
        shared_post_id=post.id
    )
    db.session.add(msg)
    db.session.commit()
    flash(f'Post successfully shared with {recipient.username}!', 'success')
    return redirect(request.referrer or url_for('main.main_page'))

@main.route("/notifications/read", methods=['POST'])
@login_required
def read_notifications():
    for notif in current_user.notifications.filter_by(is_read=False).all():
        notif.is_read = True
    db.session.commit()
    return jsonify({"status": "success"})
