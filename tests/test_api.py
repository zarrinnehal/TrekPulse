import pytest
from datetime import date, timedelta
from app import db
from app.models import User, Trek
from werkzeug.security import generate_password_hash

@pytest.fixture
def setup_api_data(app):
    with app.app_context():
        # Create trek
        trek = Trek(
            name='API Trek',
            location='Online',
            difficulty='Easy',
            duration=1,
            total_slots=10,
            available_slots=10,
            status='Open',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=2)
        )
        db.session.add(trek)

        # Create trekker
        trekker = User(
            username='trek_api',
            email='trek_api@test.com',
            password_hash=generate_password_hash('Password123!'),
            role='trekker',
            status='approved'
        )
        db.session.add(trekker)

        # Create admin
        admin = User(
            username='admin_api',
            email='admin_api@test.com',
            password_hash=generate_password_hash('Password123!'),
            role='admin',
            status='approved'
        )
        db.session.add(admin)
        db.session.commit()

        yield {
            'trekker_email': 'trek_api@test.com',
            'admin_email': 'admin_api@test.com'
        }

def test_api_get_treks(client, setup_api_data):
    # Public read-only access to treks
    response = client.get('/api/treks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'API Trek'

def test_api_unauthorized_bookings(client, setup_api_data):
    # Anonymous request to /api/bookings should redirect to login (Flask-Login behaviour)
    response_anon = client.get('/api/bookings')
    assert response_anon.status_code == 302 # redirect to login

    # Log in as trekker
    with client:
        client.post('/auth/login', data={
            'email': setup_api_data['trekker_email'],
            'password': 'Password123!'
        })
        
        # Trekker request to /api/bookings should return 403 Forbidden
        response_trekker = client.get('/api/bookings')
        assert response_trekker.status_code == 403

def test_api_admin_bookings_and_users(client, setup_api_data):
    # Log in as admin
    with client:
        client.post('/auth/login', data={
            'email': setup_api_data['admin_email'],
            'password': 'Password123!'
        })
        
        response_bookings = client.get('/api/bookings')
        assert response_bookings.status_code == 200
        assert isinstance(response_bookings.get_json(), list)

        response_users = client.get('/api/users')
        assert response_users.status_code == 200
        users_list = response_users.get_json()
        assert len(users_list) == 2 # trek_api and admin_api (excluding the seeded one, or including all)
