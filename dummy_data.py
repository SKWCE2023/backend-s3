from faker import Faker
import random
from app import db, app, Company

fake = Faker()

def create_company_dummy_data():
    with app.app_context():
        for _ in range(10):
            company = Company(
                name=fake.company(),
                address=fake.address(),
                tin=random.randint(1000000, 9999999),
                rs=fake.random_letters(length=10),
                bic=fake.random_letters(length=10)
            )
            db.session.add(company)
        db.session.commit()
    print('Company dummy data added successfully')

create_company_dummy_data()