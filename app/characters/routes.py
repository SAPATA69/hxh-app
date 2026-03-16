from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from ..models import db, Character
import base64

characters = Blueprint('characters', __name__)

NEN_TYPES = [
    ('Enhancement',    'สายเสริมพลัง'),
    ('Emission',       'สายแผ่พุ่ง'),
    ('Transmutation',  'สายเปลี่ยนแปลง'),
    ('Conjuration',    'สายแปรสภาพ'),
    ('Manipulation',   'สายควบคุม'),
    ('Specialization', 'สายพิเศษ'),
]

def save_image(file):
    """แปลงไฟล์รูปเป็น base64 string"""
    if file and file.filename != '':
        data = file.read()
        ext = file.filename.rsplit('.', 1)[-1].lower()
        mime = f'image/{ext}' if ext != 'jpg' else 'image/jpeg'
        return f'data:{mime};base64,{base64.b64encode(data).decode()}'
    return None

# -------------------- INDEX --------------------
@characters.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    nen_filter = request.args.get('nen_type', '')

    query = Character.query
    if search:
        query = query.filter(Character.name.ilike(f'%{search}%'))
    if nen_filter:
        query = query.filter(Character.nen_type_en == nen_filter)

    chars = query.order_by(Character.name).all()
    return render_template('characters/index.html',
                           characters=chars,
                           nen_types=NEN_TYPES,
                           search=search,
                           nen_filter=nen_filter)

# -------------------- ADD --------------------
@characters.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        nen_en = request.form.get('nen_type_en')
        nen_th = dict(NEN_TYPES).get(nen_en, '')

        image_data = save_image(request.files.get('image'))

        char = Character(
            name        = request.form.get('name'),
            nen_type_en = nen_en,
            nen_type_th = nen_th,
            ability     = request.form.get('ability'),
            description = request.form.get('description'),
            image       = image_data,
        )
        db.session.add(char)
        db.session.commit()
        flash(f'เพิ่ม {char.name} สำเร็จแล้วครับ!', 'success')
        return redirect(url_for('characters.index'))

    return render_template('characters/add.html', nen_types=NEN_TYPES)

# -------------------- EDIT --------------------
@characters.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    char = Character.query.get_or_404(id)

    if request.method == 'POST':
        nen_en = request.form.get('nen_type_en')
        char.name        = request.form.get('name')
        char.nen_type_en = nen_en
        char.nen_type_th = dict(NEN_TYPES).get(nen_en, '')
        char.ability     = request.form.get('ability')
        char.description = request.form.get('description')

        # อัปเดตรูปเฉพาะตอนที่มีการอัปโหลดใหม่
        new_image = save_image(request.files.get('image'))
        if new_image:
            char.image = new_image

        db.session.commit()
        flash(f'แก้ไข {char.name} สำเร็จแล้วครับ!', 'success')
        return redirect(url_for('characters.index'))

    return render_template('characters/edit.html', character=char, nen_types=NEN_TYPES)

# -------------------- DELETE --------------------
@characters.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    char = Character.query.get_or_404(id)
    db.session.delete(char)
    db.session.commit()
    flash(f'ลบ {char.name} แล้วครับ', 'warning')
    return redirect(url_for('characters.index'))