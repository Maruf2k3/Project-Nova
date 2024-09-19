from app_init import create_initialized_flask_app
from routes import register_routes

app , socketio = create_initialized_flask_app()

register_routes(app ,socketio)

if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)
