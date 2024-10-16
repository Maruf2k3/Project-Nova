from app_init import create_initialized_flask_app
from routes import register_routes


app = create_initialized_flask_app()

# register_routes(app ,socketio)
register_routes(app)

if __name__ == "__main__":
     app.run(app, debug=True, host='0.0.0.0', port=8080)
