from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User

auth_bp = Blueprint('auth', __name__)

#Signup
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    #If already logged in, go to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('study.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        #Validation
        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'error')
            return render_template('signup.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('signup.html')

        #checked if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('signup.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('signup.html')

        #Create new user
        #generate_password_hash turns password into a long random string
        new_user = User(
            username = username,
            email = email,
            password = generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('study.dashboard'))

    return render_template('signup.html')