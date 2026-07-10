import pytest
from datetime import date, timedelta
from app import db
from app.models import User, Trek, Booking, StaffProfile
from werkzeug.security import generate_password_hash

@pytest.fixture
def setup_staff_and_trek(app):
    with app.app_context():
        # Create approved staff member
        staff = User(
            username='guide_john',
            email='john@guide.com',
            password_hash=generate_password_hash('Password123!'),
            role='staff',
            status='approved'
        )
        db.session.add(staff)
        db.session.flush()

        profile = StaffProfile(
            user_id=staff.id,
            name='John Doe',
            contact_details='john@social'
        )
        db.session.add(profile)

        # Create another staff member
        other_staff = User(
            username='guide_other',
            email='other@guide.com',
            password_hash=generate_password_hash('Password123!'),
            role='staff',
            status='approved'
        )
        db.session.add(other_staff)
        db.session.flush()

        # Create a trek assigned to John
        trek_john = Trek(
            name='John Expedition',
            location='Nepal',
            difficulty='Hard',
            duration=12,
            total_slots=10,
            available_slots=10,
            status='Approved',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=22),
            assigned_staff_id=staff.id
        )
        db.session.add(trek_john)

        # Create a trek assigned to Other guide
        trek_other = Trek(
            name='Other Expedition',
            location='Alps',
            difficulty='Moderate',
            duration=5,
            total_slots=8,
            available_slots=8,
            status='Approved',
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=10),
            assigned_staff_id=other_staff.id
        )
        db.session.add(trek_other)
        db.session.commit()

        yield {
            'staff_id': staff.id,
            'staff_email': 'john@guide.com',
            'trek_john_id': trek_john.id,
            'trek_other_id': trek_other.id
        }

def test_staff_dashboard(client, setup_staff_and_trek):
    # Log in as John
    with client:
        client.post('/auth/login', data={
            'email': setup_staff_and_trek['staff_email'],
            'password': 'Password123!'
        })
        
        response = client.get('/staff/')
        assert response.status_code == 200
        assert b'John Expedition' in response.data
        assert b'Other Expedition' not in response.data  # Should only show assigned treks

def test_staff_edit_own_trek(client, setup_staff_and_trek, app):
    # Log in as John
    with client:
        client.post('/auth/login', data={
            'email': setup_staff_and_trek['staff_email'],
            'password': 'Password123!'
        })

        # Load edit page
        response_get = client.get(f"/staff/trek/{setup_staff_and_trek['trek_john_id']}/edit")
        assert response_get.status_code == 200

        # Submit updates
        response_post = client.post(f"/staff/trek/{setup_staff_and_trek['trek_john_id']}/edit", data={
            'available_slots': '7',
            'status': 'Open'
        }, follow_redirects=True)
        assert response_post.status_code == 200

        # Verify database update
        with app.app_context():
            trek = db.session.get(Trek, setup_staff_and_trek['trek_john_id'])
            assert trek.available_slots == 7
            assert trek.status == 'Open'

def test_staff_unauthorized_access(client, setup_staff_and_trek):
    # Log in as John
    with client:
        client.post('/auth/login', data={
            'email': setup_staff_and_trek['staff_email'],
            'password': 'Password123!'
        })

        # Try to edit other guide's trek (should return 403 Forbidden)
        response_edit = client.get(f"/staff/trek/{setup_staff_and_trek['trek_other_id']}/edit")
        assert response_edit.status_code == 403

        # Try to view participants of other guide's trek (should return 403 Forbidden)
        response_part = client.get(f"/staff/trek/{setup_staff_and_trek['trek_other_id']}/participants")
        assert response_part.status_code == 403
