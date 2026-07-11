from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models import Trek, Booking, User

api_bp = Blueprint('api', __name__)

@api_bp.route('/treks', methods=['GET'])
def get_treks():
    treks = Trek.query.all()
    treks_list = []
    for t in treks:
        treks_list.append({
            'id': t.id,
            'name': t.name,
            'location': t.location,
            'difficulty': t.difficulty,
            'duration': t.duration,
            'total_slots': t.total_slots,
            'available_slots': t.available_slots,
            'status': t.status,
            'start_date': t.start_date.strftime('%Y-%m-%d'),
            'end_date': t.end_date.strftime('%Y-%m-%d'),
            'assigned_staff_id': t.assigned_staff_id
        })
    return jsonify(treks_list)

@api_bp.route('/bookings', methods=['GET'])
@login_required
def get_bookings():
    # Only Admin can view all bookings via API
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    bookings = Booking.query.all()
    bookings_list = []
    for b in bookings:
        bookings_list.append({
            'id': b.id,
            'user_id': b.user_id,
            'trek_id': b.trek_id,
            'booking_date': b.booking_date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': b.status
        })
    return jsonify(bookings_list)

@api_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    # Only Admin can view all users via API
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    users = User.query.all()
    users_list = []
    for u in users:
        users_list.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'status': u.status,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(users_list)
