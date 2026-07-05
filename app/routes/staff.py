from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, Trek, Booking
from app.forms import StaffTrekUpdateForm

staff_bp = Blueprint('staff', __name__)

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'staff':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@staff_bp.route('/')
@login_required
@staff_required
def dashboard():
    treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()
    
    assigned_count = len(treks)
    total_participants = 0
    open_count = 0
    
    trek_stats = []
    for trek in treks:
        registered_count = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
        total_participants += registered_count
        if trek.status == 'Open':
            open_count += 1
            
        trek_stats.append({
            'trek': trek,
            'registered_count': registered_count
        })
        
    return render_template(
        'staff/dashboard.html',
        treks_data=trek_stats,
        assigned_count=assigned_count,
        total_participants=total_participants,
        open_count=open_count
    )

@staff_bp.route('/trek/<int:trek_id>/edit', methods=['GET', 'POST'])
@login_required
@staff_required
def edit_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        flash('Trek not found.', 'danger')
        return redirect(url_for('staff.dashboard'))

    # Security: Ensure only the assigned staff member can manage this trek
    if trek.assigned_staff_id != current_user.id:
        abort(403)

    form = StaffTrekUpdateForm()
    
    if form.validate_on_submit():
        new_avail = form.available_slots.data
        new_status = form.status.data

        # Business Rules Validation
        if new_avail < 0:
            flash('Available slots cannot be negative.', 'danger')
            return render_template('staff/edit_trek.html', form=form, trek=trek)

        # Count active bookings for slot validation
        active_bookings_count = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
        
        # Max available slots cannot exceed capacity minus bookings
        max_possible_avail = trek.total_slots - active_bookings_count
        if new_avail > max_possible_avail:
            flash(f'Available slots cannot exceed remaining capacity ({max_possible_avail}).', 'danger')
            return render_template('staff/edit_trek.html', form=form, trek=trek)

        trek.available_slots = new_avail
        trek.status = new_status
        db.session.commit()
        flash('Trek updated successfully!', 'success')
        return redirect(url_for('staff.dashboard'))

    if request.method == 'GET':
        form.available_slots.data = trek.available_slots
        form.status.data = trek.status

    return render_template('staff/edit_trek.html', form=form, trek=trek)

@staff_bp.route('/trek/<int:trek_id>/participants')
@login_required
@staff_required
def view_participants(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        flash('Trek not found.', 'danger')
        return redirect(url_for('staff.dashboard'))

    # Security: Ensure only the assigned staff member can manage this trek
    if trek.assigned_staff_id != current_user.id:
        abort(403)

    bookings = Booking.query.filter_by(trek_id=trek_id, status='Booked').all()
    return render_template('staff/participants.html', trek=trek, bookings=bookings)

@staff_bp.route('/trek/<int:trek_id>/start', methods=['POST'])
@login_required
@staff_required
def start_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.assigned_staff_id != current_user.id:
        abort(403)
    trek.status = 'Started'
    db.session.commit()
    flash(f'Trek {trek.name} has been marked as Started!', 'success')
    return redirect(url_for('staff.edit_trek', trek_id=trek.id))

@staff_bp.route('/trek/<int:trek_id>/complete', methods=['POST'])
@login_required
@staff_required
def complete_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.assigned_staff_id != current_user.id:
        abort(403)
    trek.status = 'Completed'
    # Automatically mark all active bookings as Completed for history tracking
    bookings = Booking.query.filter_by(trek_id=trek_id, status='Booked').all()
    for b in bookings:
        b.status = 'Completed'
    db.session.commit()
    flash(f'Trek {trek.name} has been marked as Completed!', 'success')
    return redirect(url_for('staff.edit_trek', trek_id=trek.id))

@staff_bp.route('/my-treks')
@login_required
@staff_required
def my_treks():
    treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()
    trek_stats = []
    for trek in treks:
        registered_count = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
        trek_stats.append({
            'trek': trek,
            'registered_count': registered_count
        })
    return render_template('staff/my_treks.html', treks_data=trek_stats)

@staff_bp.route('/participants')
@login_required
@staff_required
def all_participants():
    treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()
    trek_ids = [t.id for t in treks]
    bookings = Booking.query.filter(Booking.trek_id.in_(trek_ids), Booking.status == 'Booked').all() if trek_ids else []
    return render_template('staff/all_participants.html', bookings=bookings)

@staff_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@staff_required
def profile():
    from app.forms import ProfileForm
    from werkzeug.security import generate_password_hash
    form = ProfileForm(user_id=current_user.id)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('staff.profile'))

    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('staff/profile.html', form=form)
