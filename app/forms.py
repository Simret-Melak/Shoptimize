from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,SelectField,IntegerField, DecimalField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    position = SelectField('Position',
                           choices=[('manager', 'Store Manager'), ('cashier', 'Cashier'), ('admin', 'Administrator')],
                           validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    position = SelectField('Position',
                           choices=[('manager', 'Store Manager'), ('cashier', 'Cashier'), ('admin', 'Administrator')],
                           validators=[DataRequired()])

class ItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    unit = StringField('Unit of Measure', validators=[DataRequired()])
    type = StringField('Type', validators=[DataRequired()])
    quantity = DecimalField('Quantity', validators=[DataRequired()])
    price = DecimalField('Price', validators=[DataRequired()])
    submit = SubmitField('Add Item')

class SearchForm(FlaskForm):
    search = StringField('Search by ID or Name', validators=[DataRequired()])
    submit = SubmitField('Search')

class AddToCartForm(FlaskForm):
    item_id = IntegerField('Item ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Add to Cart')
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


