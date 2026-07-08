from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from datetime import datetime
from app.models import Trek, Booking
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    difficulty = request.args.get('difficulty', '')
    search = request.args.get('search', '')

    query = Trek.query.filter(Trek.status.in_(['Approved', 'Open']))

    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    if search:
        query = query.filter(
            (Trek.name.ilike(f'%{search}%')) | 
            (Trek.location.ilike(f'%{search}%'))
        )

    treks = query.all()
    return render_template('main/index.html', treks=treks, difficulty=difficulty, search=search, datetime=datetime)

@main_bp.route('/trek/<int:trek_id>')
def trek_details(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        flash('Trek route not found.', 'danger')
        return redirect(url_for('main.index'))
    
    already_booked = False
    if current_user.is_authenticated and current_user.role == 'trekker':
        booking = Booking.query.filter_by(
            user_id=current_user.id,
            trek_id=trek_id,
            status='Booked'
        ).first()
        if booking:
            already_booked = True

    return render_template('main/trek_details.html', trek=trek, already_booked=already_booked)
