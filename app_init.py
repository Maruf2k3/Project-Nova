import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

# Initialize database, login manager, and JWT manager
db = SQLAlchemy()
login_manager = LoginManager()
jwt = JWTManager()
# Add this to your app initialization
socketio = SocketIO()

def create_initialized_flask_app():
    app = Flask(__name__, static_folder='static')

    # Set secret keys and database URI
    app.config['SECRET_KEY'] = 'your-secret-key'
    database_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'pos_system.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'another-secret-key'

    # Configuration for file uploads
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    # Ensure the upload directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    # Initialize SocketIO with your app
    socketio.init_app(app)

    # Load user
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    return app, socketio
