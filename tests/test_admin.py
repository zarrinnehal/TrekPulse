import pytest
from datetime import date, timedelta
from app import db
from app.models import User, Trek, Booking, StaffProfile
from werkzeug.security import generate_password_hash

@pytest.fixture
def logged_in_admin_client(client, app):
    with app.app_context():
        # Create and seed admin user
        admin = User(
            username='admin_test',
            email='admin_test@test.com',
            password_hash=generate_password_hash('AdminPass123!'),
            role='admin',
            status='approved'
        )
        db.session.add(admin)
        db.session.commit()

    # Log in admin
    with client:
        client.post('/auth/login', data={
            'email': 'admin_test@test.com',
            'password': 'AdminPass123!'
        })
        yield client

def test_admin_dashboard_access(logged_in_admin_client):
    response = logged_in_admin_client.get('/admin/')
    assert response.status_code == 200
    assert b'Admin Administration' in response.data

def test_create_trek_route(logged_in_admin_client, app):
    start = date.today() + timedelta(days=5)
    end = start + timedelta(days=4)
    
    response = logged_in_admin_client.post('/admin/trek/new', data={
        'name': 'Glacier Trail Trek',
        'location': 'Montana, USA',
        'difficulty': 'Hard',
        'duration': '5',
        'total_slots': '15',
        'start_date': start.strftime('%Y-%m-%d'),
        'end_date': end.strftime('%Y-%m-%d'),
        'status': 'Approved',
        'assigned_staff_id': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        trek = Trek.query.filter_by(name='Glacier Trail Trek').first()
        assert trek is not None
        assert trek.location == 'Montana, USA'
        assert trek.difficulty == 'Hard'
        assert trek.duration == 5
        assert trek.total_slots == 15
        assert trek.available_slots == 15
        assert trek.status == 'Approved'

def test_edit_trek_route(logged_in_admin_client, app):
    # Setup a trek route first
    with app.app_context():
        trek = Trek(
            name='Scenic Route',
            location='Utah',
            difficulty='Easy',
            duration=3,
            total_slots=10,
            available_slots=10,
            status='Pending',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=4)
        )
        db.session.add(trek)
        db.session.commit()
        trek_id = trek.id

    # Update trek details via Admin route
    start = date.today() + timedelta(days=2)
    end = start + timedelta(days=3)
    response = logged_in_admin_client.post(f'/admin/trek/edit/{trek_id}', data={
        'name': 'Scenic Route Updated',
        'location': 'Utah, USA',
        'difficulty': 'Moderate',
        'duration': '4',
        'total_slots': '12',
        'start_date': start.strftime('%Y-%m-%d'),
        'end_date': end.strftime('%Y-%m-%d'),
        'status': 'Open',
        'assigned_staff_id': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        updated_trek = db.session.get(Trek, trek_id)
        assert updated_trek.name == 'Scenic Route Updated'
        assert updated_trek.difficulty == 'Moderate'
        assert updated_trek.status == 'Open'
        assert updated_trek.total_slots == 12

def test_approve_and_blacklist_staff(logged_in_admin_client, app):
    # Setup pending staff guide
    with app.app_context():
        staff_user = User(
            username='guide_pending',
            email='pending@guide.com',
            password_hash=generate_password_hash('Password123!'),
            role='staff',
            status='pending'
        )
        db.session.add(staff_user)
        db.session.commit()
        staff_id = staff_user.id

    # Approve staff
    response_approve = logged_in_admin_client.post(f'/admin/staff/approve/{staff_id}', follow_redirects=True)
    assert response_approve.status_code == 200
    with app.app_context():
        user = db.session.get(User, staff_id)
        assert user.status == 'approved'

    # Blacklist staff
    response_blacklist = logged_in_admin_client.post(f'/admin/user/blacklist/{staff_id}', follow_redirects=True)
    assert response_blacklist.status_code == 200
    with app.app_context():
        user = db.session.get(User, staff_id)
        assert user.status == 'blacklisted'
