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
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
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
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_out = db.Column(db.DateTime, nullable=True)

    @property
    def worked_hours(self):
        if self.clock_out:
            worked_time = self.clock_out - self.clock_in
            total_minutes = int(worked_time.total_seconds() / 60)
            hours, minutes = divmod(total_minutes, 60)
            if hours > 0:
                return f"{hours} hour(s), {minutes} minute(s)"
            else:
                return f"{minutes} minute(s)"
        return None
    
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_due = db.Column(db.Float, default=0.0)  # Amount the group owes
    total_paid = db.Column(db.Float, default=0.0)  # Total amount paid by the group

    # Relation to track group payments
    payments = db.relationship('GroupPayment', backref='related_group', lazy=True)

    # Relation to track group sales
    sales = db.relationship('GroupSale', backref='related_group', lazy=True)


class GroupSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    items = db.Column(db.Text, nullable=False)  # Store items as JSON (item name, quantity, price)
    subtotal = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, nullable=False)
    grand_total = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, nullable=True, default=0.0)
    payment_method = db.Column(db.String(50) , nullable=False)
    server = db.Column(db.String(100), nullable=False)  # Added server field
    # New notes field
    notes = db.Column(db.String(255), nullable=True, default='')

    # Foreign key to reference the Group
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)

    # The group that this sale belongs to
    group = db.relationship('Group', backref=db.backref('group_sales', lazy=True))


class GroupPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    date_paid = db.Column(db.DateTime)

    # Relationship with Group
    group = db.relationship('Group', backref=db.backref('group_payments', lazy=True))

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0.0)  # Total stock
    unit = db.Column(db.String(20), nullable=False)  # Unit like kg, liters, etc.

    def add_quantity(self, amount):
        """Method to add quantity when new stock arrives."""
        self.quantity += amount

    def subtract_quantity(self, amount):
        """Method to subtract quantity when stock is used."""
        self.quantity -= amount if self.quantity >= amount else 0

class InventoryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    used_quantity = db.Column(db.Float, nullable=False)
    inventory_item = db.relationship('Inventory', backref='usage_logs')






