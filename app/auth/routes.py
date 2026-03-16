from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..models import db, User

auth = Blueprint('auth', __name__)

# -------------------- REGISTER --------------------
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('characters.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email    = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('ชื่อผู้ใช้นี้มีอยู่แล้วครับ', 'danger')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('อีเมลนี้มีอยู่แล้วครับ', 'danger')
            return redirect(url_for('auth.register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('สมัครสมาชิกสำเร็จ! เข้าสู่ระบบได้เลยครับ', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# -------------------- LOGIN --------------------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('characters.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'ยินดีต้อนรับ {user.username}!', 'success')
            return redirect(url_for('characters.index'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้องครับ', 'danger')

    return render_template('auth/login.html')


# -------------------- LOGOUT --------------------
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ออกจากระบบแล้วครับ', 'info')
    return redirect(url_for('auth.login'))


# -------------------- ADMIN USERS --------------------
@auth.route('/admin/users')
@login_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('auth/admin_users.html', users=users)