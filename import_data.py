from app import db, app, Service, Users, Customers
import csv
import xml.etree.ElementTree as ET
from datetime import datetime

def import_services_data():
    with app.app_context():
        Service.query.delete()
        try:
            with open('./import_files/services.csv', 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                next(csv_reader, None)
                # Ensure that the order of columns in the CSV file matches the order of fields in Services model
                for row in csv_reader:
                    service = Service(
                        code = row[0],
                        service = row[1],
                        price = row[2]
                    )
                    db.session.add(service)
                    db.session.commit()
            print('Services data imported successfully')
        except Exception as e:
            print(f'Error importing Services data: {e}')

def import_users_data():
    with app.app_context():
        Users.query.delete()
        try:
            with open('./import_files/users.csv', 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                next(csv_reader, None)
                # Ensure that the order of columns in the CSV file matches the order of fields in Users model
                for row in csv_reader:
                    full_name = row[1].split()
                    user = Users(
                        first_name = full_name[0],
                        last_name = full_name[1],
                        login = row[2],
                        password = row[3],
                        ip = row[4],
                        last_login = datetime.strptime(row[5], '%m/%d/%Y').strftime('%Y-%m-%d'),
                        services_offered = row[6],
                        role = row[7],
                    )
                    db.session.add(user)
                    db.session.commit()
            print('Users data imported successfully')
        except Exception as e:
            print(f'Error importing Users data: {e}')

def import_customers_data():
    with app.app_context():
        Customers.query.delete()
        try:
            tree = ET.parse('./import_files/clients.xml')
            root = tree.getroot()
            for item in root.findall('record'):
                full_name = item.find('fullname').text.split() 
                customer = Customers(
                    first_name = full_name[0],
                    last_name = full_name[1],
                    login = item.find('login').text,
                    password = item.find('pwd').text,
                    email = item.find('email').text,
                    guid = item.find('guid').text,
                    ip = item.find('ipadress').text,
                    social_sec_number = item.find('social_sec_number').text,
                    ein = item.find('ein').text,
                    social_type = item.find('social_type').text,
                    country = item.find('country').text,
                    phone = item.find('phone').text,
                    passport_series = item.find('passport_s').text,
                    passport_number = item.find('passport_n').text,
                    dob_timestamp = item.find('birthdate_timestamp').text,
                    insurance_name = item.find('insurance_name').text,
                    insurance_address = item.find('insurance_address').text,
                    insurance_inn = item.find('insurance_inn').text,
                    insurance_policy = item.find('insurance_pc').text,
                    insurance_bik = item.find('insurance_bik').text,
                    user_agent = item.find('ua').text
                )
                db.session.add(customer)
                db.session.commit()
            print('Customers data imported successfully')
        except Exception as e:
            print(f'Error importing customers data: {e}')

def create_temp_administrators():
    with app.app_context():
        try:
            administrators = [
                {
                    'first_name': 'Shubham',
                    'last_name': 'Expert',
                    'login': 'expertSK',
                    'password': 'root',
                    'ip': '127.0.0.1',
                    'last_login': '2023-11-24',
                    'type': '4',
                    'services_offered': []
                },
                {
                    'first_name': 'Kirti',
                    'last_name': 'Competitor',
                    'login': 'competitorK',
                    'password': 'root',
                    'ip': '127.0.0.1',
                    'last_login': '2022-11-24',
                    'type': '4',
                    'services_offered': []
                }
            ]
            for row in administrators:
                user = Users(
                    first_name = row['first_name'],
                    last_name = row['last_name'],
                    login = row['login'],
                    password = row['password'],
                    ip = row['ip'],
                    last_login = row['last_login'],
                    role = row['type'],
                    services_offered = row['services_offered'],
                )
                db.session.add(user)
                db.session.commit()
            print('Administrator added successfully')
        except Exception as e:
            print(f'Error adding administrator: {e}')

import_services_data()
import_users_data()
import_customers_data()
create_temp_administrators()