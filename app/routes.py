from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm,ItemForm,SearchForm
from app.models import User,Item,Sold
from flask import jsonify

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
        if user.position not in ['manager', 'cashier', 'admin']:
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
    # Check if the current user is authenticated and is a manager
    if not current_user.is_authenticated or current_user.position != 'manager':
        flash('You must be a manager to access this page.')
        return redirect(url_for('index'))

    form = ItemForm()
    if form.validate_on_submit():
        # Search for an existing item with the same name
        existing_item = Item.query.filter_by(name=form.name.data).first()

        if existing_item:
            # If the item exists, update its attributes
            existing_item.unit = form.unit.data
            existing_item.type = form.type.data
            existing_item.quantity = form.quantity.data
            existing_item.price = form.price.data
            flash('Item details have been updated.')
        else:
            # If the item does not exist, create a new item
            new_item = Item(
                name=form.name.data,
                unit=form.unit.data,
                type=form.type.data,
                quantity=form.quantity.data,
                price=form.price.data
            )
            db.session.add(new_item)
            flash('The new item has been added!')

        # Commit changes to the database
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_item.html', title='Add New Item', form=form)



@app.route('/search_items', methods=['GET', 'POST'])
def search_items():
    form = SearchForm()
    items = Item.query  # Start with all items

    if form.validate_on_submit():
        search_query = form.search.data
        if search_query.isdigit():  # If the search query is numeric, assume it's an id
            items = items.filter(Item.id == int(search_query))
        else:  # Otherwise, search by name
            items = items.filter(Item.name.ilike(f'%{search_query}%'))

    items = items.all()  # Execute the query to retrieve the items

    return render_template('search_items.html', title='Search Items', form=form, items=items)

@app.route('/search_items_cashier', methods=['GET', 'POST'])
def search_items_cashier():
    form = SearchForm()
    items = Item.query  # Start with all items

    if form.validate_on_submit():
        search_query = form.search.data
        if search_query.isdigit():  # If the search query is numeric, assume it's an id
            items = items.filter(Item.id == int(search_query))
        else:  # Otherwise, search by name
            items = items.filter(Item.name.ilike(f'%{search_query}%'))

    items = items.all()  # Execute the query to retrieve the items

    return render_template('search_items_cashier.html', title='Search Items Cashier', form=form, items=items)

@app.route('/sell_item', methods=['POST'])
@login_required  # If login is required
def sell_item():
    item_id = request.form.get('item_id', type=int)
    sell_quantity = request.form.get('sell_quantity', type=int)

    item = Item.query.get(item_id)
    if not item or item.quantity < sell_quantity:
        flash('Invalid item or insufficient quantity.')
        return redirect(url_for('search_items_cashier'))

    item.quantity -= sell_quantity
    sale = Sold(quantity=sell_quantity, item_id=item_id, cashier_id=current_user.id)
    db.session.add(item)
    db.session.add(sale)

    try:
        db.session.commit()
        flash('Sale successful.')
    except Exception as e:
        db.session.rollback()
        flash('Error processing sale.')
        # Optionally log the error for debugging: app.logger.error('Error: %s', e)

    return redirect(url_for('search_items_cashier'))


@app.route('/scarce_item', methods=['GET', 'POST'])
@login_required
def scarce_item():
    # Define the threshold for scarcity
    scarcity_threshold = 10

    # Fetch items whose quantity is below the threshold
    scarce_items = Item.query.filter(Item.quantity < scarcity_threshold).all()

    # Render a template, passing the scarce items
    return render_template('scarce_items.html', items=scarce_items)
