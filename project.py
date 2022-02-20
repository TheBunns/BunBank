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
    accounts = db.relationship('Account', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'Nama <{self.name}>'
    
class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    branch_name = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(200), unique=True, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    accounts = db.relationship('Account', backref='branch', lazy='dynamic')
    
    def __repr__(self):
        return f'Cabang <{self.branch_name}>'
    
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    number = db.Column(db.String(15), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    # transfers = db.relationship('Transfer', backref='account', lazy='dynamic')
    withdraws = db.relationship('Withdraw', backref='account', lazy='dynamic')
    saves = db.relationship('Save', backref='account', lazy='dynamic')

    def __repr__(self):
        return f'Rekening <{self.number}>'
    
class Transfer(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    from_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    to_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    nominal = db.Column(db.Integer, nullable=False)
    from_account = db.relationship('Account', backref="from", uselist=False, foreign_keys=[from_account_id])
    to_account = db.relationship('Account', backref="to", uselist=False, foreign_keys=[to_account_id])
    
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

def parsed_user_pass():
    encoded = request.headers.get('Authorization')
    encodedStr = encoded[6:]
    decodedBytes = base64.b64decode(encodedStr)
    decodedStr = str(decodedBytes, "utf-8")
    
    for i in range(len(decodedStr)):
        if decodedStr[i] == ":":
            password = decodedStr[(i+1):]
            username = decodedStr[:i]
    
    return [username, password]

@app.route('/')
def home():
    return {
        'message':'Selamat datang di BunBank'
    }
    
@app.route('/admin', methods=['POST'])
def create_admin():
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    data = request.get_json()
    adm = User.query.filter_by(name=username).first()
    if not adm:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif adm.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    elif adm.is_admin == False:
        return jsonify({
            'Message': 'anda tidak diizinkan'
        }), 400
    elif not 'username' in data or not 'password' in data or not 'email' in data:
        return jsonify({
			'error': 'Bad Request',
			'message': 'Please enter the data correctly'
		}), 400
    
    adm = User(
        name = data['username'],
        email = data['email'],
        password = data['password'],
        is_admin = True
    )
    db.session.add(adm)
    db.session.commit()
    
    return {
		'User': adm.name, 
		'message': 'Telah ditambahkan sebagai admin'
	}, 201
    
@app.route('/user', methods=['POST'])
def create_user():
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    data = request.get_json()
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    elif user.is_admin == False:
        return jsonify({
            'Message': 'anda tidak diizinkan'
        }), 400
    elif not 'username' in data or not 'password' in data or not 'email' in data:
        return jsonify({
			'error': 'Bad Request',
			'message': 'Tolong masukan data dengan benar'
		}), 400
    
    u = User(
        name = data['username'],
        email = data['email'],
        password = data['password'],
        is_admin = False
    )
    db.session.add(u)
    db.session.commit()
    
    return {
		'User': u.name, 
		'message': 'Berhasil ditambahkan'
	}, 201
    
@app.route('/change-data/user/<id>', methods=['PUT'])
def update_data_user(id):
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    data = request.get_json()
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    elif user.is_admin == False:
        return jsonify({
            'Message': 'anda tidak diizinkan'
        }), 400
    
    u = User.query.filter_by(id=id).first_or_404()
    
    if 'username' in data:
        u.name = data['username']
    elif 'email' in data:
        u.email = data['email']
    elif 'password' in data:
        u.password = data['password']
    
    db.session.commit()
    
    return {
		'Message': 'Data telah berhasil diubah'
	}, 201
    
@app.route('/change-password/user', methods=['PUT'])
def change_password_user():
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    data = request.get_json()
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'user yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah',
            'asd' : password
        }), 400
    elif not 'old_password' in data:
        return jsonify({
            'message': 'password lama anda salah'
        }), 400
    
    user.password = data['new_password']
    
    db.session.commit()
    
    return {
		'Message': 'Password telah berhasil diubah'
	}, 201
    
@app.route('/delete/user/<id>', methods=['DELETE'])
def delete_user(id):
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    elif user.is_admin == False:
        return jsonify({
            'Message': 'anda tidak izinkan'
        }), 400
    
    u = User.query.filter_by(id=id).first_or_404()
    
    db.session.delete(u)
    db.session.commit()
    
    return {
		'Message': 'User berhasil dihapus'
	}, 201
    
@app.route('/branch', methods=['POST'])
def create_branch():
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    data = request.get_json()
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    elif user.is_admin == False:
        return jsonify({
            'Message': 'anda tidak diizinkan'
        }), 400
    elif not 'branch_name' in data or not 'address' in data or not 'city' in data:
        return jsonify({
			'error': 'Bad Request',
			'message': 'Tolong masukan data dengan benar'
		}), 400
    
    b = Branch(
        branch_name = data['branch_name'],
        address = data['address'],
        city = data['city']
    )
    db.session.add(b)
    db.session.commit()
    
    return {
		'Branch': b.branch_name, 
		'message': 'Berhasil ditambahkan'
	}, 201
    
@app.route('/change-data/branch/<id>', methods=['PUT'])
def update_data_branch(id):
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    data = request.get_json()
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    elif user.is_admin == False:
        return jsonify({
            'Message': 'anda tidak diizinkan'
        }), 400
    
    branch = Branch.query.filter_by(id=id).first_or_404()
    
    if 'branch_name' in data:
        branch.branch_name = data['branch_name']
    elif 'address' in data:
        branch.address = data['address']
    elif 'city' in data:
        branch.city = data['city']
    
    db.session.commit()
    
    return {
		'Message': 'Data telah berhasil diubah'
	}, 201

@app.route('/delete/branch/<id>', methods=['DELETE'])
def delete_branch(id):
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    elif user.is_admin == False:
        return jsonify({
            'Message': 'anda tidak izinkan'
        }), 400
    
    branch = Branch.query.filter_by(id=id).first_or_404()
    
    db.session.delete(branch)
    db.session.commit()
    
    return {
		'Message': 'branch berhasil dihapus'
	}, 201
    
@app.route('/account', methods=['POST'])
def create_account():
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    data = request.get_json()
    u = User.query.filter_by(name=data['username']).first()
    b = Branch.query.filter_by(branch_name=data['branch_name']).first()
    number = Account.query.filter_by(number=data['number']).first()
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    elif user.is_admin == False:
        return jsonify({
            'Message': 'anda tidak diizinkan'
        }), 400
    elif not 'username' in data or not 'branch_name' in data or not 'number' in data or not 'balance' in data:
        return jsonify({
			'error': 'Bad Request',
			'message': 'Tolong masukan data dengan benar'
		}), 400
    elif not u:
        return jsonify({
            'Message': 'Tidak ada user dengan username tersebut'
        }), 400
    elif not b:
        return jsonify({
            'Message': 'Tidak ada Branch dengan nama tersebut'
        }), 400
    elif len(data['number']) < 10:
        return jsonify({
            'Message': 'Nomor rekening harus 10 digit atau lebih'
        }), 400
    elif number != None:
        return jsonify({
            'Message': 'Nomor rekening tersebut sudah ada'
        }), 400
    elif data['balance'] < 50000:
        return jsonify({
            'Message': 'saldo awal minimal RP.50.000'
        }), 400
    
    a = Account(
        number = data['number'],
        user_id = u.id,
        branch_id = b.id,
        balance = data['balance'],
        status = "Aktif"
    )
    db.session.add(a)
    db.session.commit()
    
    return {
		'User': u.name, 
        'Account': data['number'],
        'branch': b.branch_name,
		'message': 'Account berhasil ditambahkan'
	}, 201
    
@app.route('/change-data/account/<id>', methods=['PUT'])
def update_data_account(id):
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    data = request.get_json()
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    elif user.is_admin == False:
        return jsonify({
            'Message': 'anda tidak diizinkan'
        }), 400
    
    account = Account.query.filter_by(id=id).first_or_404()

    if 'branch_name' in data:
        b = Branch.query.filter_by(branch_name=data['branch_name']).first()
        account.branch_id = b.id
    elif 'username' in data:
        u = User.query.filter_by(name=data['username']).first()
        account.user_id = u.id
    elif 'number' in data:
        account.number = data['number']
    
    db.session.commit()
    
    return {
		'Message': 'Data telah berhasil diubah'
	}, 201
    
@app.route('/delete/account/<id>', methods=['DELETE'])
def delete_account(id):
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    elif user.is_admin == False:
        return jsonify({
            'Message': 'anda tidak izinkan'
        }), 400
    
    account = Account.query.filter_by(id=id).first_or_404()
    
    db.session.delete(account)
    db.session.commit()
    
    return {
		'Message': 'branch berhasil dihapus'
	}, 201
    
@app.route('/close-account/user', methods=['PUT'])
def close_account_user():
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    
    account = Account.query.filter_by(user_id=user.id).first_or_404()
    
    account.status = 'Close'
    
    db.session.commit()
    
    return {
		'Message': 'Rekening telah ditutup'
	}, 201

@app.route('/close-account/user/<id>', methods=['PUT'])
def close_account_admin(id):
    parsed = parsed_user_pass()
    username = parsed[0]
    password = parsed[1]
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            'Message': 'username yang anda masukan salah'
        }), 400
    elif user.password != password:
        return jsonify({
            'message': 'password yang anda masukan salah'
        }), 400
    elif user.is_admin == False:
        return jsonify({
            'Message': 'anda tidak diizinkan'
        }), 400
    
    account = Account.query.filter_by(id=id).first_or_404()
    
    account.status = 'Close'
    
    db.session.commit()
    
    return {
		'Message': 'Data telah berhasil diubah'
	}, 201

if __name__ == '__main__':
	app.run()