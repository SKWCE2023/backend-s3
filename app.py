from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import ForeignKey, exc, or_
from flask_session import Session
from datetime import datetime
import phonenumbers
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/shubs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer)
    service = db.Column(db.Text)
    price = db.Column(db.Float)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    login = db.Column(db.String(50))
    password = db.Column(db.String(50))
    ip = db.Column(db.String)
    last_login = db.Column(db.Date)
    role = db.Column(db.Integer)
    services_offered = db.Column(JSON)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(254))
    address = db.Column(db.Text)
    tin = db.Column(db.Integer)
    rs = db.Column(db.String(50))
    bic = db.Column(db.String(50))

class Customers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    login = db.Column(db.String(50))
    password = db.Column(db.String(50))
    guid = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(254))
    ip = db.Column(db.String, nullable=True)
    social_sec_number = db.Column(db.String(30), nullable=True)
    ein = db.Column(db.String(50), nullable=True)
    social_type = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String)
    passport_series = db.Column(db.Integer)
    passport_number = db.Column(db.Integer)
    dob_timestamp = db.Column(db.String(50), nullable=True)
    insurance_name = db.Column(db.String(50), nullable=True)
    insurance_address = db.Column(db.Text, nullable=True)
    insurance_inn = db.Column(db.String(50), nullable=True)
    insurance_policy = db.Column(db.String(50), nullable=True)
    insurance_bik = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    company_name = db.Column(db.String(254), nullable=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_code = db.Column(db.String(50), nullable=True)
    cost = db.Column(db.Float, nullable=True)
    creation_date = db.Column(db.DateTime, server_default=db.func.now())
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    order_status = db.Column(db.String(50), default="")
    service_status = db.Column(db.String(50))
    order_completion_time = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    company_name = db.Column(db.String(254), nullable=True)

class LoginHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_login = db.Column(db.String(50))
    user_name = db.Column(db.String(50), nullable=True)
    ip_address = db.Column(db.String)
    login_time = db.Column(db.DateTime, server_default=db.func.now())
    successful = db.Column(db.Boolean)

class ServiceRendered(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    platform = db.Column(db.String(100))
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    performed_at = db.Column(db.DateTime, server_default=db.func.now())
    completion_date = db.Column(db.DateTime, nullable=True)
    avg_deviation = db.Column(db.Float, nullable=True)

class UtilizerOperation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    order_received_at = db.Column(db.DateTime, server_default=db.func.now())
    service_rendered_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    execution_completed_at = db.Column(db.DateTime, nullable=True)

@app.route('/api/login', methods=['POST'])
def login():
    try:
        login_blocked_until = session.get('login_blocked_until')
        if login_blocked_until and datetime.strptime(login_blocked_until, '%Y-%m-%d %H:%M:%S') > datetime.now():
            res = {
                'status': 'error',
                'message': 'Login is blocked for 15 minutes. Please try again later.',
                'error_type': 'LoginBlockedException'
            }
            return jsonify(res), 403

        username = request.form.get('username')
        password = request.form.get('password')
        ip_address = request.remote_addr
        user = Users.query.filter_by(login=username, password=password).first()
        if user:
            full_name = f"{user.first_name} {user.last_name}"
            login_history = LoginHistory(user_login=username, user_name=full_name, ip_address=ip_address, successful=True)
            db.session.add(login_history)
            db.session.commit()
            user_data = {
                'id': user.id,
                'login': user.login,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role
            }
            return jsonify({'status': 'success', 'data': user_data}), 200
        else:
            login_history = LoginHistory(user_login=username, user_name='', ip_address=ip_address, successful=False)
            db.session.add(login_history)
            db.session.commit()
            res = {
                'status': 'error',
                'message': 'Invalid username or password. Please try again.',
                'error_type': 'InputException'
            }
            return jsonify(res), 404
    except exc.SQLAlchemyError:
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

@app.route('/api/logout', methods=['GET'])
def logout():
    try:
        time = datetime.now() + timedelta(minutes=15)
        session["login_blocked_until"] = time.strftime('%m/%d/%Y, %H:%M:%S')
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        res = {
            'status': 'error',
            'message': 'Internal Server Error',
            'error_type': 'DatabaseException'
        }
        return jsonify(res), 500

@app.route('/api/login_history', methods=['GET'])
def login_history():
    try:
        data = []
        search = request.args.get('search')
        ordering = request.args.get('ordering')
        order_by = LoginHistory.login_time.desc() if ordering == 'descending' else LoginHistory.login_time
        if search:
            data = LoginHistory.query.filter(
                or_(LoginHistory.user_name.ilike(f'%{search}%'), LoginHistory.user_login.ilike(f'%{search}%'))
            ).order_by(order_by).all()
        else:
            data = LoginHistory.query.order_by(order_by).all()
        
        history_data = []
        for entry in data:
            history_data.append({
                'id': entry.id,
                'user_login': entry.user_login,
                'user_name': entry.user_name,
                'ip_address': entry.ip_address,
                'login_time': entry.login_time.isoformat()
            })
        res = {
            'status': 'success',
            'message': None,
            'data': history_data,
            'error_type': None
        }
        return jsonify(res), 200
    except Exception as e:
        print(e)
        res = {
            'status': 'error',
            'message': 'Internal Server Error',
            'error_type': 'DatabaseException'
        }
        return jsonify(res), 500

@app.route('/api/get_last_order', methods=['GET'])
def get_last_order():
    try:
        last_order = Order.query.order_by(Order.creation_date.desc()).first()
        if last_order:
            res = {
                'status': 'success',
                'data': last_order.id,
            }
            return jsonify(res), 200
        else:
            res = {
                'status': 'error',
                'message': 'No orders found',
                'error_type': 'DoesNotExistException'
            }
            return jsonify(res), 404
    except Exception as e:
        res = {
            'status': 'error',
            'message': 'Internal Server Error',
            'error_type': 'DatabaseException'
        }
        return jsonify(res), 500

@app.route('/api/get_services', methods=['GET'])
def get_services():
    try:
        services = Service.query.all()
        data = []
        for service in services:
            data.append({
                "id": service.id,
                "code": service.code,
                "service": service.service,
                "price": service.price
            })
        res = {
            'status': 'success',
            'data': data
        }
        return jsonify(res), 200
    except Exception as e:
        print(e)
        res = {
            'status': 'error',
            'message': 'Internal Server Error',
            'error_type': 'DatabaseException'
        }
        return jsonify(res), 500

@app.route('/api/get_customers_by_name', methods=['GET'])
def get_customers_by_name():
    search = request.args.get('search')
    try:
        data = []
        customers = Customers.query.filter(Customers.first_name.ilike(f'{search}%')).all()
        for customer in customers:
            data.append({
                "name": f'{customer.first_name} {customer.last_name}',
                'id': customer.id,
                'email': customer.email,
                'phone': customer.phone,
                'company_name': customer.company_name
            })
        res = {
            'status': 'success',
            'data': data
        }
        return jsonify(res), 200
    except Exception as e:
        print(e)
        res = {
            'status': 'error',
            'message': 'Internal Server Error',
            'error_type': 'DatabaseException'
        }
        return jsonify(res), 500

@app.route('/api/create_customer', methods=['POST'])
def create_customer():
    try:
        if request.method == 'POST':
            data = request.form
            customer = Customers(
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                login=data.get('login'),
                password=data.get('password'),
                passport_series=int(data.get('passport_series')),
                passport_number=int(data.get('passport_number')),
                dob_timestamp=int(datetime.strptime(data.get('date_of_birth'), '%d/%m/%Y').timestamp()),
                phone=str(phonenumbers.parse(data.get('phone_number'), None).national_number),
                email=data.get('email'),
                guid=data.get('guid', None),
                ip=data.get('ip', None),
                social_sec_number=data.get('social_sec_number', None),
                ein=data.get('ein', None),
                social_type=data.get('social_type', None),
                country=data.get('country', None),
                insurance_name=data.get('insurance_name', None),
                insurance_address=data.get('insurance_address', None),
                insurance_inn=data.get('insurance_inn', None),
                insurance_policy=data.get('insurance_policy', None),
                insurance_bik=data.get('insurance_bik', None),
                user_agent=data.get('user_agent', None),
                company_name=data.get('company_name', None)
            )
            db.session.add(customer)
            db.session.commit()
            return jsonify({'message': 'Customer created successfully'}), 201
    except Exception as e:
        print(e)
        res = {
            'status': 'error',
            'message': 'Internal Server Error',
            'error_type': 'DatabaseException'
        }
        return jsonify(res), 500

@app.route('/api/create_company', methods=['POST'])
def create_company():
    try:
        if request.method == 'POST':
            data = request.form
            new_company = Company(
                name=data.get('name'),
                address=data.get('address'),
                tin=int(data.get('tin')),
                rs=data.get('rs'),
                bic=data.get('bic')
            )
            db.session.add(new_company)
            db.session.commit()
            return jsonify({'message': 'Company created successfully'}), 201
    except Exception as e:
        res = {
            'status': 'error',
            'message': 'Internal Server Error',
            'error_type': 'DatabaseException'
        }
        return jsonify(res), 500

@app.route('/api/create_order', methods=['POST'])
def create_order():
    try:
        if request.method == 'POST':
            bar_code = request.form.get('bar_code')
            service_id = request.form.get('service_id')
            user_id = request.form.get('user_id')
            customer_id = request.form.get('customer_id')
            cost = request.form.get('cost')
            company_name = request.form.get('company_name')
            new_order = Order(
                bar_code=bar_code,
                service_id=Service.query.get(int(service_id)).id,
                order_status="Received",
                service_status="Pending for Recycle",
                user_id=Users.query.get(int(user_id)).id,
                customer_id=Customers.query.get(int(customer_id)).id if customer_id else None,
                cost=float(cost),
                company_name=company_name
            )
            db.session.add(new_order)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Order created successfully'}), 201
    except Exception as e:
        print(e)
        res = {
            'status': 'error',
            'message': 'Internal Server Error',
            'data': None,
            'error_type': 'DatabaseException'
        }
        return jsonify(res), 500

@app.route('/api/get_services_by_period_and_customer', methods=['GET'])
def get_services_by_period_and_customer():
    try:
        start_period = request.args.get('start_period')
        end_period = request.args.get('end_period')
        customer_id = request.args.get('customer_id')
        company_name = request.args.get('company_name')
        start_date = datetime.strptime(start_period, '%Y-%m-%d')
        end_date = datetime.strptime(end_period, '%Y-%m-%d')
        if company_name:
            services = Service.query.join(Order).filter(Order.creation_date.between(start_date, end_date), Order.company_name == company_name).all()
        else:
            services = Service.query.join(Order).filter(Order.creation_date.between(start_date, end_date), Order.customer_id == int(customer_id)).all()
        service_data = [{'id': service.id, 'code': service.code, 'service': service.service, 'price': service.price}
                        for service in services]
        res = {
            'status': 'success',
            'data': service_data
        }
        return jsonify(res), 200
    except Exception as e:
        res = {
            'status': 'error',
            'message': 'Internal Server Error',
            'error_type': 'DatabaseException'
        }
        return jsonify(res), 500

@app.route('/api/get_company_by_name', methods=['GET'])
def get_company_by_name():
    company_name = request.args.get('name')
    try:
        data = []
        companies = Company.query.filter(Company.name.ilike(f'{company_name}%')).all()
        for company in companies:
            data.append({
                "name": company.name,
                'id': company.id
            })
        res = {
            'status': 'success',
            'data': data
        }
        return jsonify(res), 200
    except Exception as e:
        print(e)
        res = {
            'status': 'error',
            'message': 'Internal Server Error',
            'error_type': 'DatabaseException'
        }
        return jsonify(res), 500

@app.route('/api/get_all_orders', methods=['GET'])
def get_all_orders():
    try:
        orders = Order.query.all()
        result = []
        for order in orders:
            print(order)
            order_data = {
                'id': order.id,
                'bar_code': order.bar_code,
                'cost': order.cost,
                'creation_date': order.creation_date.isoformat(),
                'order_status': order.order_status,
                'service_status': order.service_status,
                'order_completion_time': order.order_completion_time,
                'user_id': order.user_id,
                'customer_id': order.customer_id,
                'company_name': order.company_name,
                # 'service': {
                #     'id': order.service.id,
                #     'code': order.service.code,
                #     'service': order.service.service,
                #     'price': order.service.price
                # },
                # 'user': {
                #     'id': order.user.id
                # },
                # 'customer': {
                #     'id': order.customer.id
                # }
            }
            result.append(order_data)
        return jsonify({'status': 'success', 'data': result}), 200
    except Exception as e:
        print(e)
        res = {
            'status': 'error',
            'message': 'Internal Server Error',
            'error_type': 'DatabaseException'
        }
        return jsonify(res), 500


if __name__ == '__main__':
    app.run(debug=True)