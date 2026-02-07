from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from project.models import User, Post
from project.forms import LoginForm, RegistrationForm, PostForm
from project import db

main = Blueprint('main', __name__)

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

@main.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        # Make sure author_name is in your PostForm class in forms.py
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
    
    return render_template('create_post.html', form=form, title='New Post')

@main.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('main.main_page'))

@main.route('/profile')
@login_required
def profile_page():
    return render_template('profile.html', username=current_user.username)