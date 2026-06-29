from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, StaffProfile
from app.forms import LoginForm, TrekkerRegisterForm, StaffRegisterForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.status == 'pending':
                flash('Your staff registration request is pending Admin approval.', 'warning')
                return redirect(url_for('auth.login'))
            elif user.status == 'blacklisted':
                flash('Your account has been deactivated or blacklisted by the Admin.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember.data)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Role-based redirect
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'staff':
                return redirect(url_for('staff.dashboard'))
            else:
                return redirect(url_for('trekker.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/register/trekker', methods=['GET', 'POST'])
def register_trekker():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = TrekkerRegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role='trekker',
            status='approved'
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_trekker.html', form=form)

@auth_bp.route('/register/staff', methods=['GET', 'POST'])
def register_staff():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = StaffRegisterForm()
    if form.validate_on_submit():
        # Staff is registered with status='pending'
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role='staff',
            status='pending'
        )
        db.session.add(user)
        db.session.flush()  # to get the user.id

        profile = StaffProfile(
            user_id=user.id,
            name=form.name.data,
            contact_details=form.contact_details.data
        )
        db.session.add(profile)
        db.session.commit()

        flash('Your staff registration has been submitted and is awaiting Admin approval.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_staff.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'success')
    return redirect(url_for('main.index'))
