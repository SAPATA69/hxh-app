from flask import Flask
from dotenv import load_dotenv
from .models import db, bcrypt
from flask_login import LoginManager
import os

load_dotenv()

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'กรุณาเข้าสู่ระบบก่อนครับ'

    # User loader
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .auth.routes import auth
    from .characters.routes import characters
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(characters, url_prefix='/characters')

    # Create tables
    with app.app_context():
        db.create_all()

    return app