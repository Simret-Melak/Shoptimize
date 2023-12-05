from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    position = db.Column(db.String(128))
    sold_items = db.relationship('Sold', backref='cashier', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    unit = db.Column(db.String(140))
    type = db.Column(db.String(140))
    quantity=db.Column(db.Numeric(10, 2))
    price = db.Column(db.Numeric(10, 2))
    cost_price = db.Column(db.Numeric(10, 2))
    sold_items = db.relationship('Sold',backref='item',lazy='dynamic')

    def __repr__(self):
        return '<Items {}>'.format(self.name)


class Sold(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_sold = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    quantity = db.Column(db.Integer)
    item_id = db.Column(db.Integer,db.ForeignKey('item.id'))
    cashier_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Numeric(10, 2))
    item = db.relationship('Item')
