from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from ..models import db, Character
from PIL import Image
import base64
import io

characters = Blueprint('characters', __name__)

NEN_TYPES = [
    ('Enhancement',    'สายเสริมพลัง'),
    ('Emission',       'สายแผ่พุ่ง'),
    ('Transmutation',  'สายเปลี่ยนแปลง'),
    ('Conjuration',    'สายแปรสภาพ'),
    ('Manipulation',   'สายควบคุม'),
    ('Specialization', 'สายพิเศษ'),
]

def save_image(file, max_size_kb=500, max_dimension=1024):
    """บีบอัดรูปก่อนแปลงเป็น base64 — รับได้ทุกขนาด ผลลัพธ์ไม่เกิน max_size_kb"""
    if not file or file.filename == '':
        return None

    img = Image.open(file.stream)

    # แปลงเป็น RGB เผื่อรูป PNG มี alpha channel (RGBA) หรือ palette (P)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # ย่อ dimension ถ้ากว้าง/สูงเกิน max_dimension (คงสัดส่วนไว้)
    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    # บีบ quality ลงเรื่อยๆ จนขนาดไม่เกิน max_size_kb
    quality = 85
    while quality >= 20:
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        if buffer.tell() / 1024 <= max_size_kb:
            break
        quality -= 10

    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode()
    return f'data:image/jpeg;base64,{encoded}'


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