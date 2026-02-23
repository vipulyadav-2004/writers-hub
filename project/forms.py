from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from project.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use.')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=150)])
    author_name = StringField('Author', validators=[DataRequired(), Length(max=100)])
    body = TextAreaField('Write here.....', validators=[DataRequired(), Length(min=1)], render_kw={"rows": 10})
    picture = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Publish Post')

class UpdateProfileForm(FlaskForm):
    username = StringField('Update Username', validators=[DataRequired(), Length(min=3, max=80)])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Upload Image')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')

class MessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Send')


class UpdatePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')]
    )
    submit = SubmitField('Update Password')


class UpdateEmailForm(FlaskForm):
    email = StringField('New Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Update Email')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already in use. Please choose a different one.')


class DeleteAccountForm(FlaskForm):
    confirm_text = StringField("Type 'DELETE' to confirm", validators=[DataRequired()])
    submit = SubmitField('Delete My Account')

    def validate_confirm_text(self, confirm_text):
        if confirm_text.data != 'DELETE':
            raise ValidationError("You must type exactly 'DELETE' to confirm.")

class PreferencesForm(FlaskForm):
    msg_preference = SelectField('Message Preference', choices=[('everyone', 'Everyone'), ('followers', 'Followers Only'), ('none', 'No One')])
    profile_visibility = SelectField('Profile Visibility', choices=[('public', 'Public'), ('private', 'Private')])
    two_factor_enabled = BooleanField('Enable Two-Factor Authentication')
    email_notif_enabled = BooleanField('Enable Email Notifications')
    feed_sorting = SelectField('Feed Sorting', choices=[('latest', 'Latest'), ('popular', 'Most Popular')])
    accent_color = SelectField('Accent Color', choices=[
        ('purple', 'Vibrant Purple'), 
        ('blue', 'Bright Blue'), 
        ('pink', 'Hot Pink'), 
        ('green', 'Neon Green'), 
        ('yellow', 'Cyberpunk Yellow')
    ])
    submit = SubmitField('Update Preferences')
