from email.policy import default
from enum import unique
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
import base64

app = Flask(__name__)
db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:040315@localhost:5432/BunBank?sslmode=disable'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(15), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    accounts = db.relationship('account', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'Nama <{self.name}>'
    
class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    branch_name = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(200), unique=True, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    accounts = db.relationship('account', backref='branch', lazy='dynamic')
    
    def __repr__(self):
        return f'Cabang <{self.branch_name}>'
    
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    number = db.Column(db.Integer, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    transfers = db.relationship('transfer', backref='account', lazy='dynamic')
    withdraws = db.relationship('withdraw', backref='account', lazy='dynamic')
    saves = db.relationship('save', backref='account', lazy='dynamic')

    def __repr__(self):
        return f'Rekening <{self.number}>'
    
class Transfer(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    from_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    to_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    nominal = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'Transfer sejumlah <{self.nominal}>'
    
class Withdraw(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    nominal = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    def __repr__(self):
        return f'Tarik tunai sejumlah <{self.nominal}>'
    
class Save(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    nominal = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    def __repr__(self):
        return f'Setor tunai sejumlah <{self.nominal}>'
    
# account_transfer = db.Table('account_transfer', db.Model.metadata,
#                             db.Column('transfer_id', db.ForeignKey('transfer.id'), primary_key=True),
#                             db.Column('from_account_id', db.ForeignKey('account.id'), primary_key=True),
#                             db.Column('to_account_id', db.ForeignKey('account.id'), primary_key=True)
#                             )

# account_withdraw = db.Table('account_withdraw', db.Model.metadata,
#                             db.Column('withdraw_id', db.ForeignKey('withdraw.id'), primary_key=True),
#                             db.Column('account_id', db.ForeignKey('account.id'), primary_key=True)
#                             )

# account_save = db.Table('account_save', db.Model.metadata,
#                             db.Column('save_id', db.ForeignKey('save.id'), primary_key=True),
#                             db.Column('account_id', db.ForeignKey('account.id'), primary_key=True)
#                             )

db.create_all()
db.session.commit()

@app.route('/')
def home():
    return {
        'message':'Welcome To BunBank'
    }
    


if __name__ == '__main__':
	app.run()