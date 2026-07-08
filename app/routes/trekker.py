from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, Trek, Booking
from app.forms import ProfileForm

trekker_bp = Blueprint('trekker', __name__)

def trekker_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'trekker':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@trekker_bp.route('/')
@login_required
@trekker_required
def dashboard():
    # Active bookings
    active_bookings = Booking.query.filter_by(user_id=current_user.id, status='Booked').all()
    
    # Search / Filters
    difficulty = request.args.get('difficulty', '')
    location = request.args.get('location', '')

    query = Trek.query.filter_by(status='Open')
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))

    available_treks = query.all()
    
    return render_template(
        'trekker/dashboard.html',
        bookings=active_bookings,
        treks=available_treks,
        difficulty=difficulty,
        location=location
    )

@trekker_bp.route('/book/<int:trek_id>', methods=['POST'])
@login_required
@trekker_required
def book_trek(trek_id):
    # Lock/Retrieve trek record
    trek = db.session.get(Trek, trek_id)
    if not trek:
        flash('Trek not found.', 'danger')
        return redirect(url_for('trekker.dashboard'))

    # Business Rule: User can only book if trek status is 'Open'
    if trek.status != 'Open':
        flash('Bookings are not open for this trek.', 'danger')
        return redirect(url_for('main.index'))

    # Business Rule: Prevent overbooking beyond available slots
    if trek.available_slots <= 0:
        flash('This trek is already fully booked.', 'danger')
        return redirect(url_for('main.index'))

    # Business Rule: Prevent duplicate active booking
    existing_booking = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=trek_id,
        status='Booked'
    ).first()
    if existing_booking:
        flash('You have already booked this trek.', 'warning')
        return redirect(url_for('trekker.dashboard'))

    # Create booking and decrement available slots inside database transaction
    try:
        booking = Booking(
            user_id=current_user.id,
            trek_id=trek_id,
            status='Booked'
        )
        trek.available_slots -= 1
        db.session.add(booking)
        db.session.commit()
        flash(f'Successfully booked trek: {trek.name}!', 'success')
    except Exception:
        db.session.rollback()
        flash('An error occurred during booking. Please try again.', 'danger')

    return redirect(url_for('trekker.dashboard'))

@trekker_bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
@trekker_required
def cancel_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        flash('Booking not found.', 'danger')
        return redirect(url_for('trekker.dashboard'))

    if booking.status != 'Booked':
        flash('This booking cannot be cancelled.', 'warning')
        return redirect(url_for('trekker.dashboard'))

    # Cancel booking and return slot inside transaction
    try:
        booking.status = 'Cancelled'
        booking.trek.available_slots += 1
        db.session.commit()
        flash('Your trek booking has been successfully cancelled.', 'success')
    except Exception:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')

    return redirect(url_for('trekker.dashboard'))

@trekker_bp.route('/history')
@login_required
@trekker_required
def history():
    # Fetch all historical bookings (Booked, Cancelled, Completed)
    bookings_history = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return render_template('trekker/history.html', bookings=bookings_history)

@trekker_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@trekker_required
def profile():
    form = ProfileForm(user_id=current_user.id)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Your profile details have been updated.', 'success')
        return redirect(url_for('trekker.profile'))

    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('trekker/profile.html', form=form)

@trekker_bp.route('/browse')
@login_required
@trekker_required
def browse():
    difficulty = request.args.get('difficulty', '')
    location = request.args.get('location', '')

    query = Trek.query.filter_by(status='Open')
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))

    available_treks = query.all()
    return render_template(
        'trekker/browse.html',
        treks=available_treks,
        difficulty=difficulty,
        location=location
    )

@trekker_bp.route('/bookings')
@login_required
@trekker_required
def bookings():
    all_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return render_template('trekker/bookings.html', bookings=all_bookings)
