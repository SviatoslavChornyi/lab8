
from flask import Flask, request, jsonify,make_response
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from werkzeug.security import generate_password_hash,check_password_hash
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp
import jwt
import datetime
from functools import wraps

# instantiate the app
app = Flask(__name__)
# app config
app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# instantiate db
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# instantiate manage
manager = Manager(app)
manager.add_command('db', MigrateCommand)

def check_for_token(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        token = request.args.get('token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(id=data['id']).first()

        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return wrapped
# bookorder Model
class bookorder(db.Model):

    tablename = "bookorder"

    carid = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    price = db.Column(db.Integer, db.ForeignKey('car.id'))
 
    date = db.Column(db.String(100), nullable=False)
   

    def __init__(self,  date=None):
        
        self.date = date


# User Model
class User(db.Model):
    tablename = "user"

    id = db.Column(db.Integer(), primary_key=True)
    login = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String, unique=True, nullable=False)
    username = db.Column(db.String(40), unique=True, nullable=False)
    admin = db.Column(db.Integer())

    def __init__(self, login=None, password=None, username=None,admin=None):
        self.login = login
        self.password = password
        self.username = username
        self.admin=admin


    def delete_from_db(self, id_of_d=None):
        # delete user from db by his id
        if id_of_d:
            delete_user = User.query.get(id_of_d)
            db.session.delete(delete_user)
            db.session.commit()
            return jsonify({"message": "User was deleted"}, 200)
        else:
            return jsonify({"message": "User wont deleted"}, 404)


# cars Model
class cars(db.Model):
    tablename = "cars"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(400), nullable=False)
    price = db.Column(db.Float(), nullable=False)
    amount = db.Column(db.Integer(), nullable=False)

   

    # one-to-many
   

    def __init__(self, name=None, description=None, price=None):
        self.name = name
        self.description = description
        self.price = price
        
       
        


    def delete_goods_from_db(self, id_of_g=None, name=None):
        # delete goods from db by his id
        if id_of_g:
            delete_goods = cars.query.get(id_of_g)
            delete_purchase = bookorder.query.filter_by(text=name).first()
            db.session.delete(delete_goods)
            db.session.delete(delete_purchase)
            db.session.commit()
            return jsonify({"message": "was deleted"}, 200)
        else:
            return jsonify({"message": "wont deleted"}, 404)


# User Controller
class UserController(object):
    def __init__(self, model_user=User()):
        self.model_user = model_user

    def create(self, user_data=None):
        self.model_user.login = user_data.get('login')
        self.model_user.password = user_data.get('password')
        self.model_user.username = user_data.get('name')
        self.model_user.admin=user_data.get('admin')
        user_from_db = User.query.filter_by(login=self.model_user.login).first()

        if not self.model_user.login or not self.model_user.password or not self.model_user.username:
            return jsonify({"message": "Invalid input"}, 400)
        elif user_from_db is not None:
            return jsonify({"message": "User exist with such login"}, 409)
        else:
            hash_pwd = generate_password_hash(self.model_user.password)
            data = User(self.model_user.login, hash_pwd, self.model_user.username,self.model_user.admin)
            db.session.add(data)
            db.session.commit()
            return jsonify({"message": "User was created"}, 200)


    def delete(self, id_of_d=None):
        return self.model_user.delete_from_db(id_of_d=id_of_d)


# Goods Controller
class carsController(object):
    def __init__(self, model_goods=cars()):
        self.model_goods = model_goods

    def create(self, goods_data=None):
        self.model_goods.name = goods_data.get('name')
        self.model_goods.description = goods_data.get('description')
        self.model_goods.price = goods_data.get('price')
        
       

       

        if not self.model_goods.description or not self.model_goods.name:
            return jsonify({"message": "Invalid input"}, 400)
        
        else:
            data = cars(self.model_goods.name, self.model_goods.description,self.model_goods.price)

            bookorder(data)
            db.session.add(data)
            db.session.commit()
            return jsonify({"message": "was created"}, 200)

    # by tag
    def delete(self, id_of_g=None, name=None):
        return self.model_goods.delete_goods_from_db(id_of_g=id_of_g, name=name)


# use POSTMAN post
@app.route('/UserCreate', methods=['POST'])
@check_for_token
def create_user(current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})
    user_controller = UserController()
    user_data = request.args
    return user_controller.create(user_data)


@app.route('/UserDelete', methods=['DELETE'])
@check_for_token
def delete_user():
    identifier = request.args.get('id')
    return UserController().delete(identifier)


@app.route('/carsCreate', methods=['POST'])
@check_for_token
def create_goods():
    goods_data = request.args
    return carsController().create(goods_data)


@app.route('/carsDelete', methods=['DELETE'])
@check_for_token
def delete_goods():
    identifier = request.args.get('id')
    current_name = request.args.get('name')
    return carsController().delete(identifier, current_name)

@app.route('/log_in', methods=['GET'])

def login():
    data = request.authorization

    if not data or not data.username or not data.password:
        return make_response('Could not verify1', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    user = User.query.filter_by(username=data.username).first()
    if not user:
        return make_response('Could not verify2', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    if check_password_hash(user.password, data.password):
        token = jwt.encode({'id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=25)},
                           app.config['SECRET_KEY'])

        return jsonify({'token': token.decode('UTF-8')})

    return make_response('Could not verify3', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

if __name__ == '__main__':
    app.run()