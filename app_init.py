import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager


# Initialize database, login manager, and JWT manager
db = SQLAlchemy()
login_manager = LoginManager()
jwt = JWTManager()


def create_initialized_flask_app():
    app = Flask(__name__, static_folder='static')

    # Set secret keys and database URI
    app.config['SECRET_KEY'] = 'your-secret-key'
    database_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'pos_system.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'another-secret-key'


    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)


    # Load user
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    return app
