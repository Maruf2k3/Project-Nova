import uuid
from app_init import db  # Import the same db instance from app_init.py
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timezone

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Define the MenuItem model for menu management
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)

class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_number = db.Column(db.String(50), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))  # Unique Invoice Number
    date = db.Column(db.String(50), nullable=False, default=datetime.now().strftime("%Y-%m-%d"))
    time = db.Column(db.String(50), nullable=False, default=datetime.now().strftime("%H:%M:%S"))
    items = db.Column(db.Text, nullable=False)  # Store items as JSON (item name, quantity, price)
    subtotal = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, nullable=False)
    grand_total = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, nullable=True, default=0.0)
    notes = db.Column(db.String(255), nullable=True, default='')
    server = db.Column(db.String(100), nullable=False)  # Added server field
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    payment_method = db.Column(db.String(50) , nullable=False)

    # Relationship with Customer
    customer = db.relationship('Customer', back_populates='sales')


class Customer(db.Model):
    __tablename__ = 'customer'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    
    # Back reference to the Sale model
    sales = db.relationship('Sale', back_populates='customer')


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(100), nullable=False)

    # Attendance relationship
    attendance_records = db.relationship('Attendance', backref='employee', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    clock_out = db.Column(db.DateTime, nullable=True)

    @property
    def worked_hours(self):
        if self.clock_out:
            return (self.clock_out - self.clock_in).total_seconds() / 3600  # hours worked
        return None

class ServeMenu(db.Model):
    __tablename__ = 'serve_menu'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)  # New description field
    picture = db.Column(db.String(200), nullable=True)  # Path to the image file

    def __repr__(self):
        return f"<ServeMenu {self.name}>"


