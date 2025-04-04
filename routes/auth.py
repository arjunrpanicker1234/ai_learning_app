from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User,Tutor

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        is_tutor = 'is_tutor' in request.form
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()
        
        if existing_user:
            flash('Username already exists', 'danger')
            return render_template('auth/register.html')
        
        if existing_email:
            flash('Email already registered', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        new_user.is_tutor = is_tutor  # Explicitly assign is_tutor

        
        # Add to database
        db.session.add(new_user)
        db.session.commit()  # Make sure this line is present
        
        if is_tutor:
            # Create tutor profile
            tutor_profile = Tutor(user_id=new_user.id)
            db.session.add(tutor_profile)
            db.session.commit()  # And this one too
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):  # Make sure check_password method is defined in your User model
            login_user(user)
            return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

from flask import session, flash, redirect, url_for

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Clear all session data
    flash("You have been logged out.", "success")
    return redirect(url_for('auth.login'))  # Redirect to login page
