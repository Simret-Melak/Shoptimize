from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm,ItemForm,SearchForm
from app.models import User,Item,Sold
from flask import jsonify
from sqlalchemy import desc

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

from flask import flash


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
        # Retrieve the position from the form
        desired_position = form.position.data
        # Check if the user's position matches the desired position
        if user.position != desired_position:
            flash('You do not have access to this resource as ' + desired_position)
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard')

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
        # Search for an existing item with the same name and type
        existing_item = Item.query.filter_by(name=form.name.data, type=form.type.data).first()

        if existing_item:
            # If the item exists, update its price, quantity, and add to the buying and selling prices

            existing_item.quantity += form.quantity.data
            existing_item.cost_price = form.cost_price.data
            existing_item.price = form.price.data
            flash('Item details have been updated.')
        else:
            # If the item does not exist, create a new item
            new_item = Item(
                name=form.name.data,
                unit=form.unit.data,
                type=form.type.data,
                quantity=form.quantity.data,
                price=form.cost_price.data,
                cost_price=form.price.data
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
    items = Item.query

    if form.validate_on_submit():
        search_query = form.search.data
        if search_query.isdigit():
            items = items.filter(Item.id == int(search_query))
        else:
            items = items.filter(Item.name.ilike(f'%{search_query}%'))

    items = items.all()

    return render_template('search_items.html', title='Search Items', form=form, items=items)

@app.route('/search_items_cashier', methods=['GET', 'POST'])
def search_items_cashier():
    form = SearchForm()
    items = Item.query

    if form.validate_on_submit():
        search_query = form.search.data
        if search_query.isdigit():
            items = items.filter(Item.id == int(search_query))
        else:
            items = items.filter(Item.name.ilike(f'%{search_query}%'))

    items = items.all()

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




@app.route('/top_selling_items')
@login_required
def top_selling_items():

    # if not current_user.is_authenticated or current_user.position != 'admin':
    #     flash('You must be an admin to access this page.')
    #     return redirect(url_for('index'))
    top_items = db.session.query(
        Item.name,
        db.func.sum(Sold.quantity).label('total_sold'),
        db.func.sum((Item.price - Item.cost_price) * Sold.quantity).label('total_profit')
    ).join(Sold).group_by(Item.id).order_by(desc('total_sold')).limit(10).all()

    return render_template('top_selling_items.html', title='Top Selling Items', top_items=top_items)


@app.route('/sales_and_profit', methods=['GET', 'POST'])
@login_required
def sales_and_profit():
    form = SearchForm()
    sales_query = Sold.query.join(Item).join(User).add_columns(
        Sold.id,
        Item.name,
        Item.price.label('buying_price'),
        Sold.quantity,
        (Item.price * Sold.quantity).label('selling_price'),
        ((Item.price - Item.cost_price) * Sold.quantity).label('profit')
    )


    if form.validate_on_submit() or request.form.get('search'):
        search_query = form.search.data if form.validate_on_submit() else request.form.get('search')

        if search_query:
            try:
                search_query_int = int(search_query)
                sales_query = sales_query.filter(Sold.id == search_query_int)
            except ValueError:
                sales_query = sales_query.filter(Item.name.ilike(f'%{search_query}%'))

    sales = sales_query.all()

    return render_template('sales_and_profit.html', title='Sales and Profit', form=form, sales=sales)

@app.route('/scarce_item', methods=['GET', 'POST'])
@login_required
def scarce_item():
    # Define the threshold for scarcity
    scarcity_threshold = 10

    # Fetch items whose quantity is below the threshold
    scarce_items = Item.query.filter(Item.quantity < scarcity_threshold).all()

    # Render a template, passing the scarce items
    return render_template('scarce_items.html', items=scarce_items)