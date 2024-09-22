# Project-Nova

This is a POS system for Podda Resturant

# Overview

This project is a Flask-based Point of Sale (POS) system designed for restaurant management. It includes user authentication, menu and customer management, sales tracking, and employee attendance. The project uses Flask as the backend and integrates HTML, CSS (Tailwind), and JavaScript for the frontend. It also includes real-time updates with flask_socketio for operations such as employee clock-ins and bill creation.

## Features

- **User Roles**: Admin, Manager, and Cashier
- **Menu Management**: Add, edit, delete menu items
- **Customer Management**: Add, edit, delete customers, view sales history
- **Employee Attendance**: Clock-in and clock-out functionality
- **Sales Management**: Create bills, manage payments, and generate reports
- **WebSocket Support**: Real-time notifications for new bills and employee status updates
- **Excel Uploads**: Manage menus through Excel uploads
- **JWT Authentication**: Session management for login

## Project Structure

- `app.py`: Main file to run the Flask application.
- `routes.py`: Handles the routing and logic for different endpoints (login, register, manage, etc.).
- `models.py`: Database models representing Users, Employees, Menu Items, Sales, etc.
- `templates/`: Folder containing HTML files (views) for the application.
- `static/`: Contains static files (CSS, JavaScript, images).
- `requirements.txt`: Python package dependencies.

## Prerequisites

- Python (3.7 or later)
- Node.js and npm (for frontend package management)
- SQLite (default database for Flask)

## Setup Instructions

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-repo/pos-system.git
cd pos-system
```

### Step 2: Create and Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install Frontend Dependencies with npm

```bash
npm install
```

### Step 5: Running the Application

Start the Flask application using npm start to serve both the backend and the static files:

```bash
npm start
```

You should see the application running at [http://localhost:5000](http://localhost:8080).

### Step 6: Access the Application

Open your browser and go to:

```bash
http://localhost:8080
```

Log in as an admin, manager, or cashier to access different parts of the system.

## Usage

- **Admin**: Manage users, menus, employees, and sales reports.
- **Manager**: Manage menus, customers, and sales reports.
- **Cashier**: Create bills and track sales.

## Notes

- The app does not use database migrations. The database is generated automatically when you run the app.
- The app includes WebSocket functionality for real-time updates (such as employee clock-ins and bill creation).
