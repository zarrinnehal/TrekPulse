from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, StaffProfile, Trek, Booking
from app.forms import TrekForm

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Statistics
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()

    # Chart 1: Popular Treks by Bookings
    from sqlalchemy import func
    import json
    
    top_treks_query = db.session.query(
        Trek.name, func.count(Booking.id).label('booking_count')
    ).join(Booking, Trek.id == Booking.trek_id)\
     .filter(Booking.status == 'Booked')\
     .group_by(Trek.id)\
     .order_by(func.count(Booking.id).desc())\
     .limit(5).all()

    top_treks_labels = [item[0] for item in top_treks_query]
    top_treks_data = [item[1] for item in top_treks_query]

    # Chart 2: Difficulty Distribution
    diff_query = db.session.query(
        Trek.difficulty, func.count(Trek.id)
    ).group_by(Trek.difficulty).all()

    diff_labels = [item[0] for item in diff_query]
    diff_data = [item[1] for item in diff_query]

    # Recent Bookings Table
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        recent_bookings=recent_bookings,
        top_treks_labels=json.dumps(top_treks_labels),
        top_treks_data=json.dumps(top_treks_data),
        diff_labels=json.dumps(diff_labels),
        diff_data=json.dumps(diff_data)
    )

@admin_bp.route('/treks')
@login_required
@admin_required
def manage_treks():
    q = request.args.get('q', '').strip()
    query = Trek.query
    if q:
        query = query.filter(
            (Trek.name.ilike(f'%{q}%')) | (Trek.location.ilike(f'%{q}%'))
        )
    treks = query.all()
    return render_template('admin/manage_treks.html', treks=treks, q=q)

@admin_bp.route('/staff')
@login_required
@admin_required
def manage_staff():
    pending_staff = User.query.filter_by(role='staff', status='pending').all()
    approved_staff = User.query.filter_by(role='staff', status='approved').all()
    blacklisted_staff = User.query.filter_by(role='staff', status='blacklisted').all()
    return render_template(
        'admin/manage_staff.html',
        pending_staff=pending_staff,
        approved_staff=approved_staff,
        blacklisted_staff=blacklisted_staff
    )

@admin_bp.route('/staff/approve/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_staff(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role != 'staff':
        flash('Staff member not found.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    user.status = 'approved'
    db.session.commit()
    flash(f'Staff member {user.username} has been approved.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/user/blacklist/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def blacklist_user(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role == 'admin':
        flash('Cannot blacklist this user.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    user.status = 'blacklisted'
    db.session.commit()
    flash(f'{user.role.capitalize()} {user.username} has been blacklisted.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/user/unblacklist/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def unblacklist_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Restoring staff sets status to 'approved'
    user.status = 'approved'
    db.session.commit()
    flash(f'{user.role.capitalize()} {user.username} has been restored to approved status.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/trek/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_trek():
    form = TrekForm()
    
    # Populate staff guide dropdown dynamically
    approved_staff = User.query.filter_by(role='staff', status='approved').all()
    staff_choices = [('', 'No Guide Assigned')] + [
        (str(s.id), f"{s.staff_profile.name if s.staff_profile else s.username} (ID: {s.id})") for s in approved_staff
    ]
    form.assigned_staff_id.choices = staff_choices

    if form.validate_on_submit():
        staff_id = int(form.assigned_staff_id.data) if form.assigned_staff_id.data else None
        
        trek = Trek(
            name=form.name.data,
            location=form.location.data,
            difficulty=form.difficulty.data,
            duration=form.duration.data,
            total_slots=form.total_slots.data,
            available_slots=form.total_slots.data,
            status=form.status.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            assigned_staff_id=staff_id
        )
        db.session.add(trek)
        db.session.commit()
        flash('Trek route created successfully!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/trek_form.html', form=form, title="Create Trek")

@admin_bp.route('/trek/edit/<int:trek_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        flash('Trek not found.', 'danger')
        return redirect(url_for('admin.dashboard'))

    form = TrekForm(trek_id=trek.id)
    approved_staff = User.query.filter_by(role='staff', status='approved').all()
    staff_choices = [('', 'No Guide Assigned')] + [
        (str(s.id), f"{s.staff_profile.name if s.staff_profile else s.username} (ID: {s.id})") for s in approved_staff
    ]
    form.assigned_staff_id.choices = staff_choices

    if form.validate_on_submit():
        staff_id = int(form.assigned_staff_id.data) if form.assigned_staff_id.data else None
        
        trek.name = form.name.data
        trek.location = form.location.data
        trek.difficulty = form.difficulty.data
        trek.duration = form.duration.data
        trek.status = form.status.data
        trek.start_date = form.start_date.data
        trek.end_date = form.end_date.data
        trek.assigned_staff_id = staff_id
        
        # Recalculate available slots based on bookings
        active_bookings_count = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
        trek.total_slots = form.total_slots.data
        trek.available_slots = form.total_slots.data - active_bookings_count
        
        if trek.available_slots < 0:
            db.session.rollback()
            flash('Error: Cannot reduce total slots below the number of currently active bookings.', 'danger')
            return redirect(url_for('admin.edit_trek', trek_id=trek.id))
            
        db.session.commit()
        flash('Trek details updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))

    # Populate form values for GET request
    if request.method == 'GET':
        form.name.data = trek.name
        form.location.data = trek.location
        form.difficulty.data = trek.difficulty
        form.duration.data = trek.duration
        form.total_slots.data = trek.total_slots
        form.status.data = trek.status
        form.start_date.data = trek.start_date
        form.end_date.data = trek.end_date
        form.assigned_staff_id.data = str(trek.assigned_staff_id) if trek.assigned_staff_id else ''

    return render_template('admin/trek_form.html', form=form, title="Edit Trek")

@admin_bp.route('/trek/delete/<int:trek_id>', methods=['POST'])
@login_required
@admin_required
def delete_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        flash('Trek not found.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    db.session.delete(trek)
    db.session.commit()
    flash('Trek route removed successfully.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/bookings')
@login_required
@admin_required
def view_bookings():
    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.filter_by(role='trekker').all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/search')
@login_required
@admin_required
def search():
    search_type = request.args.get('search_type', 'trek')
    q = request.args.get('q', '').strip()
    
    treks = []
    staff = []
    users = []
    
    if q:
        if search_type == 'trek':
            treks = Trek.query.filter(
                (Trek.name.ilike(f'%{q}%')) | (Trek.location.ilike(f'%{q}%'))
            ).all()
        elif search_type == 'staff':
            staff = User.query.filter_by(role='staff').join(StaffProfile, isouter=True).filter(
                (User.username.ilike(f'%{q}%')) | 
                (User.email.ilike(f'%{q}%')) | 
                (StaffProfile.name.ilike(f'%{q}%'))
            ).all()
        elif search_type == 'user':
            users = User.query.filter_by(role='trekker').filter(
                (User.username.ilike(f'%{q}%')) | (User.email.ilike(f'%{q}%'))
            ).all()
            
    return render_template(
        'admin/search.html',
        search_type=search_type,
        q=q,
        treks=treks,
        staff=staff,
        users=users
    )

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()

    from sqlalchemy import func
    import json
    
    top_treks_query = db.session.query(
        Trek.name, func.count(Booking.id).label('booking_count')
    ).join(Booking, Trek.id == Booking.trek_id)\
     .filter(Booking.status == 'Booked')\
     .group_by(Trek.id)\
     .order_by(func.count(Booking.id).desc())\
     .limit(5).all()

    top_treks_labels = [item[0] for item in top_treks_query]
    top_treks_data = [item[1] for item in top_treks_query]

    diff_query = db.session.query(
        Trek.difficulty, func.count(Trek.id)
    ).group_by(Trek.difficulty).all()

    diff_labels = [item[0] for item in diff_query]
    diff_data = [item[1] for item in diff_query]

    return render_template(
        'admin/reports.html',
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        top_treks_labels=json.dumps(top_treks_labels),
        top_treks_data=json.dumps(top_treks_data),
        diff_labels=json.dumps(diff_labels),
        diff_data=json.dumps(diff_data)
    )

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    return render_template('admin/settings.html')
