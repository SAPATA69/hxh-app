from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Character(db.Model):
    __tablename__ = 'characters'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    nen_type_en = db.Column(db.String(50), nullable=False)   # Enhancement, Emission, etc.
    nen_type_th = db.Column(db.String(50), nullable=False)   # สายเสริมพลัง, etc.
    ability     = db.Column(db.String(200))                  # ความสามารถหลัก
    description = db.Column(db.Text)                         # รายละเอียด
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Character {self.name}>'