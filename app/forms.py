from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, DateField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User, Trek

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class TrekkerRegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register as Trekker')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email address is already registered.')

class StaffRegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    contact_details = StringField('Contact Details', validators=[DataRequired(), Length(max=200)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register as Trek Staff')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email address is already registered.')

class TrekForm(FlaskForm):
    name = StringField('Trek Name', validators=[DataRequired(), Length(min=3, max=100)])
    location = StringField('Location', validators=[DataRequired(), Length(min=2, max=100)])
    difficulty = SelectField('Difficulty', choices=[('Easy', 'Easy'), ('Moderate', 'Moderate'), ('Hard', 'Hard')], validators=[DataRequired()])
    duration = IntegerField('Duration (Days)', validators=[DataRequired()])
    total_slots = IntegerField('Total Slots', validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Open', 'Open'), ('Started', 'Started'), ('Closed', 'Closed'), ('Completed', 'Completed')], validators=[DataRequired()])
    assigned_staff_id = SelectField('Assign Staff Guide', coerce=str, validators=[])
    submit = SubmitField('Save Trek')

    def __init__(self, *args, **kwargs):
        trek_id = kwargs.pop('trek_id', None)
        super(TrekForm, self).__init__(*args, **kwargs)
        self.trek_id = trek_id

    def validate_name(self, name):
        query = Trek.query.filter_by(name=name.data)
        if self.trek_id:
            query = query.filter(Trek.id != self.trek_id)
        trek = query.first()
        if trek:
            raise ValidationError('A trek with this name already exists.')

    def validate_end_date(self, end_date):
        if self.start_date.data and end_date.data < self.start_date.data:
            raise ValidationError('End date must be on or after start date.')

    def validate_total_slots(self, total_slots):
        if total_slots.data is not None and total_slots.data <= 0:
            raise ValidationError('Total slots must be greater than zero.')

class StaffTrekUpdateForm(FlaskForm):
    available_slots = IntegerField('Available Slots', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Open', 'Open'), ('Started', 'Started'), ('Closed', 'Closed'), ('Completed', 'Completed')], validators=[DataRequired()])
    submit = SubmitField('Update Trek')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('New Password (leave blank to keep current)', validators=[Length(max=128)])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('password')])
    submit = SubmitField('Update Profile')

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id', None)
        super(ProfileForm, self).__init__(*args, **kwargs)

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != self.user_id:
            raise ValidationError('Username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != self.user_id:
            raise ValidationError('Email address is already registered.')



