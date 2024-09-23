import io
import os
import csv
import uuid
from flask import json, render_template, request, redirect, url_for, flash, jsonify, Response, current_app
from flask_login import login_user, login_required, logout_user, current_user
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, set_access_cookies, set_refresh_cookies, unset_jwt_cookies
from sqlalchemy import func
from models import User, MenuItem,ServeMenu, Sale, Customer, Employee, Attendance,db
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import pytz
import openpyxl  # To handle Excel files
from flask_socketio import emit


ALLOWED_EXTENSIONS = {'xls', 'xlsx' , 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def register_routes(app , socketio):

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')


    # 1. Landing page route ("/")
    @app.route("/")
    def landing_page():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('base.html')

    # 2. Login route with JWT tokens
    @app.route("/login", methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                # Generate JWT tokens
                access_token = create_access_token(identity=user.id)
                refresh_token = create_refresh_token(identity=user.id)

                response = redirect(url_for('dashboard'))
                set_access_cookies(response, access_token)
                set_refresh_cookies(response, refresh_token)
                return response
            else:
                flash('Invalid username or password.', 'error')

        return render_template('login.html')

    # 3. Dashboard route
    @app.route("/dashboard")
    @login_required
    def dashboard():
        employees = Employee.query.all() if current_user.role == "admin" else []
        userName = current_user.username;
        return render_template("home.html", employees=employees , userName = userName)

    # 4. Register route
    # Updated Register Route with role restrictions
    @app.route("/register", methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')

            # Check if the username already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists.', 'error')
                return render_template('register.html')

            # Role restrictions logic
            if role == 'admin':
                # Check if an admin already exists
                if User.query.filter_by(role='admin').first():
                    flash('Only one admin is allowed.', 'error')
                    return render_template('register.html')

            elif role == 'manager':
                # Check if there are already two managers
                manager_count = User.query.filter_by(role='manager').count()
                if manager_count >= 2:
                    flash('Only two managers are allowed.', 'error')
                    return render_template('register.html')

            # Create a new user with the valid role
            new_user = User(username=username, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash('Registered successfully. Please log in.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')


    # 5. Logout route with token invalidation
    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        response = redirect(url_for('login'))
        unset_jwt_cookies(response)  # Unset JWT tokens
        flash('Logged out successfully.', 'success')
        return response

    # 6. Menu Management (Upload Excel and CRUD)
    @app.route("/menu-management", methods=['GET', 'POST'])
    @login_required
    def menu_management():
        if current_user.role not in ['admin', 'manager']:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            file = request.files.get('file')
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join('uploads', filename)
                file.save(filepath)

                # Read Excel and insert items into the database
                try:
                    workbook = openpyxl.load_workbook(filepath)
                    sheet = workbook.active
                    for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip the header
                        name, price, category = row
                        # Check if the item already exists in the database to prevent duplicates
                        existing_item = MenuItem.query.filter_by(name=name).first()
                        if existing_item:
                            flash(f"Item '{name}' already exists in the database.", 'warning')
                        else:
                            new_item = MenuItem(name=name, price=float(price), category=category)
                            db.session.add(new_item)
                    db.session.commit()
                    flash('Menu uploaded and saved successfully!', 'success')
                except Exception as e:
                    flash(f"An error occurred while processing the file: {str(e)}", 'error')

                # Delete the file after successful processing
                if os.path.exists(filepath):
                    os.remove(filepath)
                    flash('Uploaded file deleted successfully.', 'info')

                return redirect(url_for('menu_management'))

        menu_items = MenuItem.query.all()
        return render_template('menu_management.html', menu_items=menu_items)

    # Route for editing a menu item
    @app.route("/menu-management/edit/<int:item_id>", methods=['GET', 'POST'])
    @login_required
    def edit_menu_item(item_id):
        if current_user.role not in ['admin', 'manager']:
            return redirect(url_for('dashboard'))

        # Fetch the menu item by its ID
        menu_item = MenuItem.query.get_or_404(item_id)

        if request.method == 'POST':
            name = request.form.get('name')
            price = request.form.get('price')
            category = request.form.get('category')

            # Update the menu item with new values
            menu_item.name = name
            menu_item.price = float(price)
            menu_item.category = category

            db.session.commit()
            flash('Menu item updated successfully.', 'success')
            return redirect(url_for('menu_management'))

        return render_template('edit_menu_item.html', item=menu_item)

    @app.route("/menu-management/delete/<int:item_id>")
    @login_required
    def delete_menu_item(item_id):
        if current_user.role not in ['admin', 'manager']:
            return redirect(url_for('dashboard'))

        item = MenuItem.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash('Menu item deleted successfully!', 'success')
        return redirect(url_for('menu_management'))

    @app.route("/create-bill", methods=['GET', 'POST'])
    @login_required
    def create_bill():
        if current_user.role not in ['cashier', 'manager', 'admin']:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            # Fetch form data
            customer_id = request.form.get('customer')
              # Fetch the server name
            note = request.form.get('note')
            discount = int(request.form.get('discount', 0))
            taxFromHtml = int(request.form.get('tax', 0))
            payment_method = request.form.get('payment-method', 'cash')

            # Handle cases when no customer is selected by checking if customer_id exists
            customer = None
            if customer_id and customer_id != 'None':
                customer = Customer.query.get(customer_id)

            # Fetch items from form data (expecting JSON string of items from front-end)
            items = request.form.get('items')  # Expecting JSON string

            # Parse items as a list of dictionaries (item name, quantity, price)
            if items:
                try:
                    items = json.loads(items)
                except json.JSONDecodeError:
                    flash('Error parsing items.', 'error')
                    return redirect(url_for('create_bill'))

            # Ensure items contain 'price' and 'qty'
            if not all('price' in item and 'qty' in item for item in items):
                flash('Error: Items data is incomplete.', 'error')
                return redirect(url_for('create_bill'))

            # Calculate subtotal, tax, and grand total
            subtotal = sum(float(item['price']) * int(item['qty']) for item in items)
            tax = float(taxFromHtml/100) * subtotal 
            grand_total = subtotal + tax - discount

            # Generate a unique invoice number using uuid4
            invoice_number = str(uuid.uuid4())

            server = current_user.username

            current_time_uae = datetime.now(pytz.timezone("Asia/Dubai"))

            # Create a new Sale entry
            new_sale = Sale(
                invoice_number=invoice_number,
                date=current_time_uae.strftime("%Y-%m-%d"),
                time=current_time_uae.strftime("%H:%M:%S"),
                items=json.dumps(items),  # Storing the items as JSON in the DB
                subtotal=subtotal,
                tax=tax,
                grand_total=grand_total,
                discount=discount,
                notes=note,
                server=server,  # Store server name
                customer_id=customer.id if customer else None,  # Store customer_id only if customer exists
                payment_method=payment_method
            )

            # Add and commit the sale
            db.session.add(new_sale)
            db.session.commit()

             # Emit an event to all connected clients
            socketio.emit('new_bill_created', {'invoice_number': invoice_number}, to='/')


            flash('Bill created successfully!', 'success')
            return redirect(url_for('dashboard'))

        # Load menu items and customers, including checking if there are no customers yet
        customers = Customer.query.all() if Customer.query.count() > 0 else []
        menu_items = MenuItem.query.all()  # Ensure MenuItem is loaded

        return render_template('create_bill.html', customers=customers, menu_items=menu_items)

        # Sales Report Route
    # Register a custom Jinja filter to convert JSON strings into Python objects
    @app.template_filter('fromjson')
    def fromjson_filter(s):
        try:
            return json.loads(s)
        except (ValueError, TypeError):
            return {}

    # Sales Report Route
    @app.route("/sales-reports", methods=['GET', 'POST'])
    @login_required
    def sales_reports():
        if current_user.role not in ['admin', 'manager']:
            return redirect(url_for('dashboard'))

        sales = []
        start_date_str = None
        end_date_str = None

        if request.method == 'POST':
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')

            try:
                # Ensure dates are in the correct format
                datetime.strptime(start_date_str, '%Y-%m-%d')
                datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid date format.', 'error')
                return redirect(url_for('sales_reports'))

            # Fetch sales data within the date range
            sales = Sale.query.filter(
                func.date(Sale.date) >= start_date_str.strip(),
                func.date(Sale.date) <= end_date_str.strip()
            ).all()

            if not sales:
                flash('No sales found within the selected date range.', 'error')
                return render_template('sales_reports.html', sales=sales)

            # Render the template with sales data
            return render_template('sales_reports.html', sales=sales, start_date=start_date_str, end_date=end_date_str)

        # Render the form for GET request
        return render_template('sales_reports.html', sales=sales)

    # Route to Download Sales Report
    @app.route("/download-sales-report", methods=['GET'])
    @login_required
    def download_sales_report():
        if current_user.role not in ['admin', 'manager']:
            return redirect(url_for('dashboard'))

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if not start_date_str or not end_date_str:
            flash('Invalid date range for report download.', 'error')
            return redirect(url_for('sales_reports'))

        try:
            # Ensure dates are in the correct format
            datetime.strptime(start_date_str, '%Y-%m-%d')
            datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('sales_reports'))

        # Fetch sales data within the date range
        sales = Sale.query.filter(
            func.date(Sale.date) >= start_date_str.strip(),
            func.date(Sale.date) <= end_date_str.strip()
        ).all()

        if not sales:
            flash('No sales found within the selected date range.', 'error')
            return redirect(url_for('sales_reports'))

        # Generate the CSV data in memory
        output = io.StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerow(['Invoice Number', 'Date', 'Customer', 'Items', 'Subtotal','Tax','Discount', 'Grand Total', 'Served By','Payment Method', 'Notes'])

        for sale in sales:
            customer_name = sale.customer.name if sale.customer else "No Customer"
            items = json.loads(sale.items)

            # Handle missing 'qty' gracefully
            item_list = "; ".join([f"{item['name']} (Qty: {item.get('qty', 1)})" for item in items])

            csv_writer.writerow([
                sale.invoice_number,
                sale.date,
                customer_name,
                item_list,
                sale.subtotal,
                sale.tax,
                sale.discount,
                sale.grand_total,
                sale.server,
                sale.payment_method,
                sale.notes
            ])

        # Move to the beginning of the StringIO object
        output.seek(0)

        # Create a Response object with the CSV data
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename=salesReport_{start_date_str}_{end_date_str}.csv'
            }
        )

    # Predefined Sales Report Route for different date ranges
    @app.route("/sales-reports/predefined/<string:range_type>", methods=['GET'])
    @login_required
    def sales_reports_predefined(range_type):
        if current_user.role not in ['admin', 'manager']:
            return redirect(url_for('dashboard'))

        today = datetime.now().date()
        if range_type == 'today':
            start_date = end_date = today
        elif range_type == 'month':
            start_date = today.replace(day=1)
            end_date = today
        elif range_type == 'year':
            start_date = today.replace(month=1, day=1)
            end_date = today
        else:
            flash('Invalid range type.', 'error')
            return redirect(url_for('sales_reports'))

        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # Fetch sales data within the date range
        sales = Sale.query.filter(
            func.date(Sale.date) >= start_date_str,
            func.date(Sale.date) <= end_date_str
        ).all()

        if not sales:
            flash('No sales found for the selected range.', 'error')
            return render_template('sales_reports.html', sales=sales)

        # Render the template with sales data
        return render_template('sales_reports.html', sales=sales, start_date=start_date_str, end_date=end_date_str)

        # Customer Management route
    @app.route("/customer-management", methods=['GET', 'POST'])
    @login_required
    def customer_management():
        if current_user.role not in ['admin', 'manager']:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'add':
                # Adding a new customer
                name = request.form.get('name')
                phone_number = request.form.get('phone_number')
                new_customer = Customer(name=name, phone_number=phone_number)
                db.session.add(new_customer)
                db.session.commit()
                flash('Customer added successfully!', 'success')
            elif action == 'edit':
                # Editing an existing customer
                customer_id = request.form.get('customer_id')
                customer = Customer.query.get(customer_id)
                customer.name = request.form.get('name')
                customer.phone_number = request.form.get('phone_number')
                db.session.commit()
                flash('Customer updated successfully!', 'success')
            elif action == 'delete':
                # Deleting a customer
                customer_id = request.form.get('customer_id')
                customer = Customer.query.get(customer_id)
                db.session.delete(customer)
                db.session.commit()
                flash('Customer deleted successfully!', 'success')

        customers = Customer.query.all()
        return render_template('customer_management.html', customers=customers)


    # Route for viewing customer history
    @app.route("/customer-history", methods=['GET', 'POST'])
    @login_required
    def customer_history():
        if current_user.role not in ['admin', 'manager']:
            return redirect(url_for('dashboard'))

        customers = Customer.query.all()
        sales_history = None
        if request.method == 'POST':
            customer_id = request.form.get('customer_id')
            history_type = request.form.get('history_type')
            
            customer = Customer.query.get(customer_id)
            if history_type == 'date_range':
                start_date = request.form.get('start_date')
                end_date = request.form.get('end_date')
                sales_history = Sale.query.filter(Sale.customer_id == customer_id, Sale.date.between(start_date, end_date)).all()
            else:
                sales_history = Sale.query.filter_by(customer_id=customer_id).all()

        return render_template('customer_history.html', customers=customers, sales_history=sales_history)

        # User Management route
    @app.route("/user-management", methods=['GET', 'POST'])
    @login_required
    def user_management():
        if current_user.role != 'admin':
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            action = request.form.get('action')
            user_id = request.form.get('user_id')

            if action == 'edit':
                # Editing an existing user
                user = User.query.get(user_id)

                if not user:
                    flash('User not found!', 'error')
                    return redirect(url_for('user_management'))

                # Update role
                user.role = request.form.get('role')

                # Check if password is provided and update if necessary
                password = request.form.get('password')
                if password:
                    user.set_password(password)  # Set new password if provided

                db.session.commit()
                flash('User updated successfully!', 'success')

            elif action == 'delete':
                # Deleting a user
                user = User.query.get(user_id)

                if not user:
                    flash('User not found!', 'error')
                    return redirect(url_for('user_management'))

                db.session.delete(user)
                db.session.commit()
                flash('User deleted successfully!', 'success')

        # Fetch all users for display
        users = User.query.all()
        return render_template('user_management.html', users=users)
    

    # 1. Employee Dashboard to display all employees
    @app.route("/employees", methods=["GET", "POST"])
    @login_required
    def employee_dashboard():
        employees = Employee.query.all()

        # Adding clock-in status to employee object
        for employee in employees:
            employee.clocked_in = Attendance.query.filter_by(employee_id=employee.id, clock_out=None).first() is not None

        if request.method == 'POST':
            # Handle adding new employees
            name = request.form.get('name')
            position = request.form.get('position')
            contact_info = request.form.get('contact_info')

            new_employee = Employee(name=name, position=position, contact_info=contact_info)
            db.session.add(new_employee)
            db.session.commit()
            flash('Employee added successfully!', 'success')
            return redirect(url_for('employee_dashboard'))

        return render_template('employee_dashboard.html', employees=employees)

    # 2. Add or Edit Employee (Form View)
    @app.route("/employee/add", methods=["GET", "POST"])
    @app.route("/employee/edit/<int:employee_id>", methods=["GET", "POST"])
    @login_required
    def add_edit_employee(employee_id=None):
        employee = Employee.query.get(employee_id) if employee_id else None

        if request.method == "POST":
            name = request.form.get('name')
            position = request.form.get('position')
            contact_info = request.form.get('contact_info')

            if employee:
                # Update existing employee
                employee.name = name
                employee.position = position
                employee.contact_info = contact_info
                flash('Employee updated successfully!', 'success')
            else:
                # Add new employee
                new_employee = Employee(name=name, position=position, contact_info=contact_info)
                db.session.add(new_employee)
                flash('Employee added successfully!', 'success')

            db.session.commit()
            return redirect(url_for('employee_dashboard'))

        return render_template('add_edit_employee.html', employee=employee)

    # 3. Delete Employee
    @app.route("/employee/delete/<int:employee_id>", methods=["POST"])
    @login_required
    def delete_employee(employee_id):
        employee = Employee.query.get_or_404(employee_id)
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully!', 'success')
        return redirect(url_for('employee_dashboard'))
    
    #For The cashier
    @app.route("/e", methods=["GET"])
    @login_required
    def e():
        
        em = Employee.query.all()

        # Adding clock-in status to employee object
        for employee in em:
            employee.clocked_in = Attendance.query.filter_by(employee_id=employee.id, clock_out=None).first() is not None

        return render_template('casheirDashboard.html', employees=em)

    # 4. Clock-in route
    @app.route("/employee/clock-in/<int:employee_id>", methods=["POST"])
    @login_required
    def clock_in(employee_id):
        employee = Employee.query.get_or_404(employee_id)

        clock_in_time = datetime.now(pytz.timezone("Asia/Dubai"))
        attendance = Attendance(employee_id=employee.id, clock_in=clock_in_time)

        db.session.add(attendance)
        db.session.commit()

        # Emit the event to all clients
        socketio.emit('employee_clocked_in', {'employee_id': employee.id, 'employee_name': employee.name}, to='/')


        flash(f'{employee.name} clocked in successfully!', 'success')
        return redirect(request.referrer or url_for('dashboard'))

    # 5. Clock-out route
    @app.route("/employee/clock-out/<int:employee_id>", methods=["POST"])
    @login_required
    def clock_out(employee_id):
        attendance = Attendance.query.filter_by(employee_id=employee_id, clock_out=None).first()
        if attendance:
            clock_out_time = datetime.now(pytz.timezone("Asia/Dubai"))
            attendance.clock_out = clock_out_time
            db.session.commit()
             # Emit the event to all clients
            socketio.emit('employee_clocked_out', {'employee_id': employee_id}, to='/')

        else:
            flash('No clock-in record found for the employee.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    # 6. Employee Profile View
    @app.route("/employee/profile/<int:employee_id>", methods=["GET"])
    @login_required
    def employee_profile(employee_id):
        employee = Employee.query.get_or_404(employee_id)
        attendance_records = Attendance.query.filter_by(employee_id=employee_id).all()
        return render_template('employee_profile.html', employee=employee, attendance_records=attendance_records)

    # 7. Attendance Selection Page (select employee to view attendance)
    @app.route("/attendance/select", methods=["GET", "POST"])
    @login_required
    def attendance_selection():
        employees = Employee.query.all()

        if request.method == "POST":
            employee_id = request.form.get("employee_id")
            return redirect(url_for('employee_attendance', employee_id=employee_id))

        return render_template("attendance_selection.html", employees=employees)

    # 8. View Attendance Records (for selected employee)
    @app.route("/employee/attendance/<int:employee_id>", methods=["GET"])
    @login_required
    def employee_attendance(employee_id):
        employee = Employee.query.get_or_404(employee_id)
        attendance_records = Attendance.query.filter_by(employee_id=employee_id).all()
        return render_template('employee_attendance.html', employee=employee, attendance_records=attendance_records)

    # Serve Menu Route
    @app.route('/serveMenu', methods=['GET'])
    @login_required
    def serve_menu():
        categories = db.session.query(ServeMenu.category).distinct().all()
        categories = [c[0] for c in categories]
        menu_items = ServeMenu.query.all()
        return render_template('serveMenu.html', categories=categories, menu_items=menu_items)

    # Serve Menu Admin Route
    @app.route('/serveMenuAdmin', methods=['GET', 'POST'])
    @login_required
    def serve_menu_admin():
        if current_user.role != 'admin':
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            # Handle CRUD operations
            action = request.form.get('action')
            if action == 'add':
                # Add new menu item
                name = request.form.get('name')
                category = request.form.get('category')
                price = request.form.get('price')
                description = request.form.get('description')
                picture_file = request.files.get('picture')
                picture_filename = None
                if picture_file and allowed_file(picture_file.filename):
                    picture_filename = secure_filename(picture_file.filename)
                    picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture_filename)
                    picture_file.save(picture_path)

                new_item = ServeMenu(
                    name=name,
                    category=category,
                    price=price,
                    description=description,
                    picture=picture_filename
                )
                db.session.add(new_item)
                db.session.commit()
                flash('Menu item added successfully.', 'success')
            elif action == 'edit':
                # Edit existing menu item
                item_id = request.form.get('item_id')
                item = ServeMenu.query.get(item_id)
                if item:
                    item.name = request.form.get('name')
                    item.category = request.form.get('category')
                    item.price = request.form.get('price')
                    item.description = request.form.get('description')
                    picture_file = request.files.get('picture')
                    if picture_file and allowed_file(picture_file.filename):
                        # Delete old picture if exists
                        if item.picture:
                            old_picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.picture)
                            if os.path.exists(old_picture_path):
                                os.remove(old_picture_path)
                        picture_filename = secure_filename(picture_file.filename)
                        picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture_filename)
                        picture_file.save(picture_path)
                        item.picture = picture_filename
                    db.session.commit()
                    flash('Menu item updated successfully.', 'success')
                else:
                    flash('Menu item not found.', 'error')
            elif action == 'delete':
                # Delete menu item
                item_id = request.form.get('item_id')
                item = ServeMenu.query.get(item_id)
                if item:
                    # Delete picture if exists
                    if item.picture:
                        picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.picture)
                        if os.path.exists(picture_path):
                            os.remove(picture_path)
                    db.session.delete(item)
                    db.session.commit()
                    flash('Menu item deleted successfully.', 'success')
                else:
                    flash('Menu item not found.', 'error')
            return redirect(url_for('serve_menu_admin'))

        # GET request
        menu_items = ServeMenu.query.all()
        return render_template('serveMenuAdminPage.html', menu_items=menu_items)


