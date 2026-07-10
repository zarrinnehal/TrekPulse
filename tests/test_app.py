import pytest
from app import db
from app.models import User, StaffProfile
from werkzeug.security import generate_password_hash

def test_admin_seeding(runner):
    # Test our cli seed-db command
    result = runner.invoke(args=['seed-db'])
    assert 'Admin user seeded successfully' in result.output

    # Run it again to verify duplicate guard works
    result_dup = runner.invoke(args=['seed-db'])
    assert 'Admin user already exists' in result_dup.output

def test_trekker_registration(client, app):
    # Test registration of trekker
    response = client.post('/auth/register/trekker', data={
        'username': 'trekker1',
        'email': 'trek1@test.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username='trekker1').first()
        assert user is not None
        assert user.role == 'trekker'
        assert user.status == 'approved'

def test_staff_registration(client, app):
    # Test registration of staff (should be pending)
    response = client.post('/auth/register/staff', data={
        'username': 'guide1',
        'email': 'guide1@test.com',
        'name': 'Guide One',
        'contact_details': '+12345678',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username='guide1').first()
        assert user is not None
        assert user.role == 'staff'
        assert user.status == 'pending' # Staff should start in pending status
        
        profile = StaffProfile.query.filter_by(user_id=user.id).first()
        assert profile is not None
        assert profile.name == 'Guide One'
        assert profile.contact_details == '+12345678'

def test_login_and_logout(client, app):
    # Create trekker user in database
    with app.app_context():
        user = User(
            username='testuser',
            email='test@user.com',
            password_hash=generate_password_hash('Password123!'),
            role='trekker',
            status='approved'
        )
        db.session.add(user)
        db.session.commit()

    # Log in
    with client:
        response = client.post('/auth/login', data={
            'email': 'test@user.com',
            'password': 'Password123!'
        }, follow_redirects=True)
        assert response.status_code == 200
        from flask_login import current_user
        assert current_user.is_authenticated
        assert current_user.username == 'testuser'

        # Log out
        response_logout = client.get('/auth/logout', follow_redirects=True)
        assert response_logout.status_code == 200
        assert not current_user.is_authenticated

def test_pending_staff_login_fail(client, app):
    # Create pending staff user
    with app.app_context():
        user = User(
            username='pending_guide',
            email='pending@guide.com',
            password_hash=generate_password_hash('Password123!'),
            role='staff',
            status='pending'
        )
        db.session.add(user)
        db.session.commit()

    # Attempt log in (should fail and alert user about pending status)
    response = client.post('/auth/login', data={
        'email': 'pending@guide.com',
        'password': 'Password123!'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'pending Admin approval' in response.data
