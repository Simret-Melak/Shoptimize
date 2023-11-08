
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm,ItemForm
from app.models import User,Item

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        if user.position not in ['manager', 'cashier', 'administrator']:
            flash('You do not have access to this resource.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.position = form.position.data
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/add_items', methods=['GET', 'POST'])
def add_items():
    # Check if the current user is authenticated and a manager/admin
    if not current_user.is_authenticated or current_user.position not in ['manager', 'admin']:
        flash('You must be a manager or admin to access this page.')
        return redirect(url_for('index'))

    form = ItemForm()
    if form.validate_on_submit():
        # Instantiate an Item with form data
        item = Item(
            name=form.name.data,
            unit=form.unit.data,
            type=form.type.data,
            quantity=form.quantity.data,
            price=form.price.data
        )

        db.session.add(item)
        db.session.commit()
        flash('The new item has been added!')
        return redirect(url_for('index'))


    return render_template('add_item.html', title='Add New Item', form=form)

