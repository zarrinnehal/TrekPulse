import pytest
from datetime import date, timedelta
from app import db
from app.models import User, Trek, Booking
from werkzeug.security import generate_password_hash

@pytest.fixture
def setup_trekker_and_treks(app):
    with app.app_context():
        # Create trekker user
        trekker = User(
            username='trek_jane',
            email='jane@trekker.com',
            password_hash=generate_password_hash('Password123!'),
            role='trekker',
            status='approved'
        )
        db.session.add(trekker)
        db.session.flush()

        # Create Open trek with slots
        trek_open = Trek(
            name='Open Mountain Hike',
            location='Colo',
            difficulty='Easy',
            duration=3,
            total_slots=5,
            available_slots=5,
            status='Open',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=4)
        )
        db.session.add(trek_open)

        # Create Open trek with NO slots
        trek_no_slots = Trek(
            name='Full Valley Route',
            location='California',
            difficulty='Moderate',
            duration=5,
            total_slots=10,
            available_slots=0,
            status='Open',
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=10)
        )
        db.session.add(trek_no_slots)

        # Create Approved trek (but not Open)
        trek_not_open = Trek(
            name='Closed Glacier Trek',
            location='Alaska',
            difficulty='Hard',
            duration=10,
            total_slots=8,
            available_slots=8,
            status='Approved',
            start_date=date.today() + timedelta(days=2),
            end_date=date.today() + timedelta(days=12)
        )
        db.session.add(trek_not_open)
        db.session.commit()

        yield {
            'trekker_id': trekker.id,
            'trekker_email': 'jane@trekker.com',
            'trek_open_id': trek_open.id,
            'trek_no_slots_id': trek_no_slots.id,
            'trek_not_open_id': trek_not_open.id
        }

def test_booking_open_trek_success(client, setup_trekker_and_treks, app):
    with client:
        # Log in
        client.post('/auth/login', data={
            'email': setup_trekker_and_treks['trekker_email'],
            'password': 'Password123!'
        })

        # Book the open trek
        response = client.post(f"/trekker/book/{setup_trekker_and_treks['trek_open_id']}", follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            # Check slot is decremented
            trek = db.session.get(Trek, setup_trekker_and_treks['trek_open_id'])
            assert trek.available_slots == 4

            # Check booking is created
            booking = Booking.query.filter_by(
                user_id=setup_trekker_and_treks['trekker_id'],
                trek_id=setup_trekker_and_treks['trek_open_id']
            ).first()
            assert booking is not None
            assert booking.status == 'Booked'

def test_booking_non_open_trek_fails(client, setup_trekker_and_treks, app):
    with client:
        client.post('/auth/login', data={
            'email': setup_trekker_and_treks['trekker_email'],
            'password': 'Password123!'
        })

        # Try to book non-open trek (should fail and redirect)
        response = client.post(f"/trekker/book/{setup_trekker_and_treks['trek_not_open_id']}", follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            # Slots should remain unchanged
            trek = db.session.get(Trek, setup_trekker_and_treks['trek_not_open_id'])
            assert trek.available_slots == 8
            
            # Booking should not exist
            booking = Booking.query.filter_by(
                user_id=setup_trekker_and_treks['trekker_id'],
                trek_id=setup_trekker_and_treks['trek_not_open_id']
            ).first()
            assert booking is None

def test_booking_sold_out_trek_fails(client, setup_trekker_and_treks, app):
    with client:
        client.post('/auth/login', data={
            'email': setup_trekker_and_treks['trekker_email'],
            'password': 'Password123!'
        })

        # Try to book sold out trek (should fail)
        response = client.post(f"/trekker/book/{setup_trekker_and_treks['trek_no_slots_id']}", follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            booking = Booking.query.filter_by(
                user_id=setup_trekker_and_treks['trekker_id'],
                trek_id=setup_trekker_and_treks['trek_no_slots_id']
            ).first()
            assert booking is None

def test_booking_duplicate_fails(client, setup_trekker_and_treks, app):
    with client:
        client.post('/auth/login', data={
            'email': setup_trekker_and_treks['trekker_email'],
            'password': 'Password123!'
        })

        # Book first time
        client.post(f"/trekker/book/{setup_trekker_and_treks['trek_open_id']}", follow_redirects=True)
        
        # Book second time (should fail and redirect)
        response = client.post(f"/trekker/book/{setup_trekker_and_treks['trek_open_id']}", follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            # Slots should only have decremented once
            trek = db.session.get(Trek, setup_trekker_and_treks['trek_open_id'])
            assert trek.available_slots == 4
            
            bookings_count = Booking.query.filter_by(
                user_id=setup_trekker_and_treks['trekker_id'],
                trek_id=setup_trekker_and_treks['trek_open_id'],
                status='Booked'
            ).count()
            assert bookings_count == 1

def test_cancel_booking(client, setup_trekker_and_treks, app):
    # Book the trek first in app context
    with app.app_context():
        booking = Booking(
            user_id=setup_trekker_and_treks['trekker_id'],
            trek_id=setup_trekker_and_treks['trek_open_id'],
            status='Booked'
        )
        trek = db.session.get(Trek, setup_trekker_and_treks['trek_open_id'])
        trek.available_slots -= 1
        db.session.add(booking)
        db.session.commit()
        booking_id = booking.id
        db.session.remove()  # Clearscoped session registry

    with client:
        client.post('/auth/login', data={
            'email': setup_trekker_and_treks['trekker_email'],
            'password': 'Password123!'
        })

        # Cancel the booking
        db.session.remove()  # Clear scoped session before request
        response = client.post(f"/trekker/cancel/{booking_id}", follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            db.session.remove()  # Force query to DB
            # Check slot is restored
            updated_trek = db.session.get(Trek, setup_trekker_and_treks['trek_open_id'])
            assert updated_trek.available_slots == 5

            # Check booking status is Cancelled
            updated_booking = db.session.get(Booking, booking_id)
            assert updated_booking.status == 'Cancelled'

def test_edit_profile(client, setup_trekker_and_treks, app):
    with client:
        client.post('/auth/login', data={
            'email': setup_trekker_and_treks['trekker_email'],
            'password': 'Password123!'
        })

        # Submit profile updates
        response = client.post('/trekker/profile', data={
            'username': 'jane_new',
            'email': 'jane_new@trekker.com',
            'password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            user = db.session.get(User, setup_trekker_and_treks['trekker_id'])
            assert user.username == 'jane_new'
            assert user.email == 'jane_new@trekker.com'
